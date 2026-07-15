"""Voz no Windows: TTS (SAPI, voz masculina) + STT (reconhecimento de voz).

As bibliotecas são importadas de forma preguiçosa para que o módulo possa ser
compilado/importado mesmo onde elas não estejam instaladas.
"""


def _load():
    out = {}
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
    return out


class WindowsVoice:
    def __init__(self):
        self._libs = _load()
        self.engine = None
        self._listen_thread = None
        self._stop = None
        if self._libs.get("tts"):
            try:
                self.engine = self._libs["tts"].init()
                self._apply_jarvis_voice()
            except Exception:
                self.engine = None

    def _apply_jarvis_voice(self):
        try:
            voices = self.engine.getProperty("voices")
            picked = None
            for v in voices:
                if "male" in v.name.lower() or "homem" in v.name.lower():
                    picked = v
                    break
            if not picked:
                for v in voices:
                    if "portug" in v.name.lower() or "brazil" in v.name.lower():
                        picked = v
                        break
            if picked:
                self.engine.setProperty("voice", picked.id)
            self.engine.setProperty("rate", 175)
        except Exception:
            pass

    def speak(self, text: str):
        clean = " ".join(str(text).split())
        if not clean or not self.engine:
            return
        try:
            self.engine.say(clean)
            self.engine.runAndWait()
        except Exception:
            pass

    def listen_once(self, timeout: int = 6, phrase_time: int = 8) -> str:
        """Escuta uma frase (push-to-talk). Retorna o texto ou ''."""
        sr = self._libs.get("sr")
        if not sr:
            return ""
        r = sr.Recognizer()
        try:
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, 0.5)
                audio = r.listen(src, timeout=timeout, phrase_time_limit=phrase_time)
        except Exception:
            return ""
        try:
            return r.recognize_google(audio, language="pt-BR")
        except Exception:
            return ""

    def start_continuous(self, on_phrase):
        """Escuta sempre ligado; chama on_phrase(texto) a cada frase reconhecida.
        Retorna True se iniciou."""
        sr = self._libs.get("sr")
        if not sr or self._listen_thread:
            return False
        import threading
        r = sr.Recognizer()
        self._stop = threading.Event()

        def loop():
            try:
                with sr.Microphone() as src:
                    r.adjust_for_ambient_noise(src, 0.5)
                    while not self._stop.is_set():
                        try:
                            audio = r.listen(src, timeout=2, phrase_time_limit=9)
                        except Exception:
                            continue
                        try:
                            text = r.recognize_google(audio, language="pt-BR")
                        except Exception:
                            continue
                        if text:
                            try:
                                on_phrase(text)
                            except Exception:
                                pass
            except Exception:
                pass

        self._listen_thread = threading.Thread(target=loop, daemon=True)
        self._listen_thread.start()
        return True

    def stop_continuous(self):
        if self._listen_thread:
            try:
                self._stop.set()
            except Exception:
                pass
            self._listen_thread = None
