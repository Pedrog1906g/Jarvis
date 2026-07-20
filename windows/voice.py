"""Voz no Windows: TTS (SAPI via pyttsx3 / voz masculina) + STT (SpeechRecognition).

Novidades v1.1:
  - speak_via_api(): usa o endpoint /api/voice/synthesize do backend quando o
    servidor tem TTS_PROVIDER=openai ou piper configurado. Reproduz o áudio via
    pygame (instalado como dependência opcional). Fallback automático para SAPI.
  - voz masculina PT-BR com prioridade aumentada.
"""
from __future__ import annotations
import logging
import os
import re
import sys
import threading
import time
import traceback

log = logging.getLogger("jarvis")


def _load():
    out: dict = {}
    try:
        import pyttsx3
        out["tts"] = pyttsx3
    except Exception:
        out["tts"] = None
    try:
        import speech_recognition as sr
        out["sr"] = sr
    except Exception:
        out["sr"] = None
    try:
        import pygame
        out["pygame"] = pygame
    except Exception:
        out["pygame"] = None
    return out


class WindowsVoice:
    def __init__(self, server_url: str = "", token: str = ""):
        self._libs = _load()
        self.engine = None
        self._listen_thread = None
        self._stop = None
        self._voice_name: str | None = None
        self.server_url = server_url.rstrip("/")
        self.token = token
        self._tts_provider: str | None = None  # detectado via /api/plugins/voice/info

        if self._libs.get("tts"):
            try:
                # Em exe congelado (pyinstaller) o SAPI/pyttsx3 precisa do COM
                # inicializado na thread principal para não falhar silenciosamente.
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass
                self.engine = self._libs["tts"].init()
                self._apply_jarvis_voice()
            except Exception:
                self.engine = None

        # Inicializa pygame mixer (para reprodução de áudio da API)
        pg = self._libs.get("pygame")
        if pg:
            try:
                pg.mixer.init()
            except Exception:
                pass

    # ── SAPI (voz local) ─────────────────────────────────────────────────────

    def _apply_jarvis_voice(self):
        try:
            voices = self.engine.getProperty("voices")
            picked = None
            male_keys = ["male", "homem", "ricardo", "daniel", "antonio",
                         "antônio", "gustavo", "felipe", "marcos", "bruno",
                         "rafael", "lucas", "diego", "pedro"]
            for v in voices:
                n = (v.name or "").lower()
                if any(k in n for k in male_keys):
                    picked = v; break
            if not picked:
                for v in voices:
                    n = (v.name or "").lower()
                    if any(k in n for k in ["portug", "brazil", "brasil", "português"]):
                        picked = v; break
            if not picked and voices:
                picked = voices[0]
            if picked:
                self.engine.setProperty("voice", picked.id)
                self._voice_name = picked.name
            self.engine.setProperty("rate", 140)  # um pouco mais lento = tom mais grave/serio
            self.engine.setProperty("volume", 1.0)
        except Exception:
            self._voice_name = None

    def voice_name(self) -> str | None:
        return self._voice_name

    def ensure_engine(self) -> bool:
        if self.engine:
            return True
        try:
            if self._libs.get("tts"):
                self.engine = self._libs["tts"].init()
                self._apply_jarvis_voice()
                return True
        except Exception:
            self.engine = None
        return False

    def _sapi_speak(self, text: str) -> bool:
        if not text.strip():
            return False
        if not self.engine and not self.ensure_engine():
            return False
        try:
            parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
            if not parts:
                parts = [text]
            for i, part in enumerate(parts):
                self.engine.say(part)
                self.engine.runAndWait()
                if i < len(parts) - 1:
                    time.sleep(0.14)
            return True
        except Exception:
            try:
                self.engine = None
                if self.ensure_engine() and self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    return True
            except Exception:
                log.warning("TTS SAPI falhou: %s", traceback.format_exc())
            return False

    # ── API TTS (servidor) ────────────────────────────────────────────────────

    def fetch_tts_provider(self):
        """Detecta o provedor TTS do servidor (openai / piper / android)."""
        if not self.server_url or not self.token:
            self._tts_provider = "android"
            return
        try:
            import requests
            r = requests.get(
                self.server_url + "/api/plugins/voice/info",
                headers={"Authorization": "Bearer " + self.token},
                timeout=8,
            )
            if r.ok:
                self._tts_provider = r.json().get("provider", "android")
                log.info("TTS provider do servidor: %s", self._tts_provider)
        except Exception:
            self._tts_provider = "android"

    def speak_via_api(self, text: str) -> bool:
        """Sintetiza texto via /api/voice/synthesize e reproduz com pygame.
        Retorna True se conseguiu reproduzir, False caso contrário (use SAPI como fallback)."""
        if not self.server_url or not self.token:
            return False
        if self._tts_provider not in ("openai", "piper"):
            return False
        pg = self._libs.get("pygame")
        if not pg:
            return False
        try:
            import requests, io
            r = requests.post(
                self.server_url + "/api/voice/synthesize",
                headers={"Authorization": "Bearer " + self.token,
                         "Content-Type": "application/json"},
                json={"text": text},
                timeout=30,
            )
            if r.status_code == 204:
                return False  # servidor sinalizou: usar TTS local
            if not r.ok:
                return False
            audio_bytes = r.content
            if len(audio_bytes) < 100:
                return False
            buf = io.BytesIO(audio_bytes)
            pg.mixer.music.load(buf)
            pg.mixer.music.play()
            while pg.mixer.music.get_busy():
                time.sleep(0.05)
            return True
        except Exception as e:
            log.warning("speak_via_api falhou: %s", e)
            return False

    # ── System.Speech (.NET) via PowerShell — TTS principal no Windows ───────
    def _powershell_speak(self, text: str) -> bool:
        """TTS principal e mais confiável no Windows: usa System.Speech.Synthesis
        do .NET (vem com o Windows, não depende do pyttsx3/SAPI do Python e NÃO
        falha silenciosamente dentro do .exe congelado). Escolhe a voz em
        português (Brasil) quando disponível e fala o texto com segurança."""
        try:
            import subprocess, base64
            # Texto em base64 (UTF-8) evita qualquer problema de aspas/acentos.
            b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
            # Script PowerShell (será passado como -EncodedCommand, também base64).
            script = (
                "Add-Type -AssemblyName System.speech;"
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "$v=$s.GetInstalledVoices()|Where-Object{$_.VoiceInfo.Culture.Name-like'pt-BR*'}|Select-Object -First 1;"
                "if($v){$s.SelectVoice($v.VoiceInfo.Name)};"
                "$s.Rate=0;"
                "$txt=[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('%s'));"
                "$s.Speak($txt)"
            ) % b64
            enc = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
            flags = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
            subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", enc],
                           timeout=120, **flags)
            return True
        except Exception as e:
            log.warning("TTS PowerShell falhou: %s", e)
            return False

    # ── Falar (método público) ────────────────────────────────────────────────

    def speak(self, text: str):
        clean = " ".join(str(text).split())
        if not clean:
            return
        # 1) TTS do servidor (openai/piper), se configurado
        if self.speak_via_api(clean):
            return
        # 2) System.Speech (.NET) via PowerShell — funciona SEMPRE no Windows,
        #    inclusive dentro do .exe congelado (o pyttsx3/SAPI costuma falhar
        #    silenciosamente no exe: sem erro e sem som). Por isso vem antes.
        if self._powershell_speak(clean):
            return
        # 3) SAPI local (pyttsx3) como reserva final
        self._sapi_speak(clean)

    # ── STT ──────────────────────────────────────────────────────────────────

    def listen_once(self, timeout: int = 5) -> str:
        sr = self._libs.get("sr")
        if not sr:
            return ""
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as mic:
                recognizer.adjust_for_ambient_noise(mic, duration=0.4)
                audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=12)
            return recognizer.recognize_google(audio, language="pt-BR")
        except Exception:
            return ""

    def start_continuous(self, on_phrase: "callable[[str], None]") -> threading.Event:
        """Inicia escuta contínua em thread daemon. Retorna Event de parada."""
        sr = self._libs.get("sr")
        if not sr:
            return threading.Event()
        stop = threading.Event()
        self._stop = stop

        def _loop():
            recognizer = sr.Recognizer()
            while not stop.is_set():
                try:
                    with sr.Microphone() as mic:
                        recognizer.adjust_for_ambient_noise(mic, duration=0.3)
                        audio = recognizer.listen(mic, timeout=4, phrase_time_limit=14)
                    text = recognizer.recognize_google(audio, language="pt-BR")
                    if text:
                        on_phrase(text)
                except sr.WaitTimeoutError:
                    continue
                except Exception:
                    time.sleep(0.5)

        threading.Thread(target=_loop, daemon=True).start()
        return stop

    def stop_continuous(self):
        if self._stop:
            self._stop.set()
            self._stop = None
