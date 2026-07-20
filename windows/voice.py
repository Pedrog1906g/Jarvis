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
        falha silenciosamente dentro do .exe congelado).

        Voz: procura uma voz MASCULINA e PROFUNDA (pt-BR se houver, senão qualquer
        masculina disponível — ex.: Microsoft David/Mark, timbre grave). Ritmo um
        pouco mais lento para soar mais natural/humano."""
        try:
            import subprocess, base64
            b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
            script = (
                "Add-Type -AssemblyName System.speech;"
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "$vs=$s.GetInstalledVoices();$best=$null;"
                "foreach($v in $vs){$n=$v.VoiceInfo.Name.ToLower();$c=$v.VoiceInfo.Culture.Name;"
                "if($c-like'pt-BR*' -and ($n -match 'david|mark|daniel|ricardo|antonio|francisco|thiago|male|homem|bruce|george|felipe')){$best=$v;break}};"
                "if(-not $best){foreach($v in $vs){$n=$v.VoiceInfo.Name.ToLower();if($n -match 'david|mark|daniel|ricardo|antonio|francisco|thiago|male|homem|bruce|george|felipe'){$best=$v;break}};}"
                "if(-not $best){foreach($v in $vs){if($v.VoiceInfo.Culture.Name -like 'pt-BR*'){$best=$v;break}};}"
                "if($best){$s.SelectVoice($best.VoiceInfo.Name)};"
                "$s.Rate=-1;"
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

    def _clean_for_speech(self, text: str) -> str:
        """Remove marcações de markdown, emojis e links para a leitura soar
        natural (sem o JARVIS 'ler' asteriscos e caracteres estranhos)."""
        import re
        t = text or ""
        t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
        t = re.sub(r"\*(.+?)\*", r"\1", t)
        t = re.sub(r"`(.+?)`", r"\1", t)
        t = re.sub(r"#+\s*", "", t)
        t = re.sub(r"https?://\S+", "link", t)
        t = re.sub(r"[*_~`#>|]", " ", t)
        t = "".join(ch for ch in t
                    if not (0x1F000 <= ord(ch) <= 0x1FAFF
                            or 0x2600 <= ord(ch) <= 0x27BF
                            or 0xFE00 <= ord(ch) <= 0xFE0F))
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def speak(self, text: str):
        clean = self._clean_for_speech(" ".join(str(text).split()))
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
            # Rápido E preciso: corta a escuta logo após o fim da fala
            # (pause_threshold menor) e ajusta o ruído só por um instante.
            recognizer.pause_threshold = 0.5
            recognizer.phrase_time_limit = 10
            recognizer.operation_timeout = 8
            with sr.Microphone() as mic:
                try:
                    recognizer.adjust_for_ambient_noise(mic, duration=0.2)
                except Exception:
                    pass
                audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=10)
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
        recognizer = sr.Recognizer()
        # Para ser rápido: para de escutar logo após o fim da fala e limita a frase.
        recognizer.pause_threshold = 0.5
        recognizer.phrase_time_limit = 8
        recognizer.operation_timeout = 8
        # Ajusta o ruído do ambiente UMA vez (não a cada loop) — menos espera.
        mic = sr.Microphone()
        try:
            with mic as m:
                recognizer.adjust_for_ambient_noise(m, duration=0.5)
        except Exception:
            pass

        def _loop():
            while not stop.is_set():
                try:
                    with mic as m:
                        audio = recognizer.listen(m, timeout=3, phrase_time_limit=8)
                    text = recognizer.recognize_google(audio, language="pt-BR")
                    if text:
                        on_phrase(text)
                except sr.WaitTimeoutError:
                    continue
                except Exception:
                    time.sleep(0.3)

        threading.Thread(target=_loop, daemon=True).start()
        return stop

    # ── Wake word (detecção de "Jarvis"/"Nexus") ─────────────────────────────
    @staticmethod
    def heard_wakeword(text: str):
        """Verifica se a frase contém a wake word, com tolerância a sotaque e a
        pequenas variações de pronúncia. Retorna:
          None -> não ouviu a wake word (ignora)
          ''   -> ouviu só a wake word (ex.: "Jarvis")
          str  -> comando após a wake word (ex.: "que horas são")
        """
        import unicodedata

        def norm(s: str) -> str:
            return unicodedata.normalize("NFKD", s or "").encode(
                "ascii", "ignore").decode("ascii").lower()

        t = norm(text)
        wake = None
        for kw in ("jarvis", "jarv", "nexus", "nex", "xarvis", "charvis",
                   "iarvis", "iarv", "jarvls"):
            if kw in t:
                wake = kw
                break
        if not wake:
            return None
        idx = t.find(wake)
        cmd = t[idx + len(wake):].strip(" ,.-:;!?")
        return cmd

    def stop_continuous(self):
        if self._stop:
            self._stop.set()
            self._stop = None
