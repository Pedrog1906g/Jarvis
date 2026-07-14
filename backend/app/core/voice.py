import os
from typing import Optional
from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_STT_MODEL, TTS_PROVIDER, OPENAI_TTS_API_KEY, DEMO_MODE

_stt_client = None
if GROQ_API_KEY:
    from openai import OpenAI
    _stt_client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcrição via Whisper na Groq. Retorna texto."""
    if DEMO_MODE or _stt_client is None:
        return "[DEMO] (áudio recebido — conecte a Groq para transcrição real)"
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        tmp = f.name
    try:
        with open(tmp, "rb") as af:
            resp = _stt_client.audio.transcriptions.create(
                model=GROQ_STT_MODEL,
                file=(filename, af, "audio/webm"),
                language="pt",
            )
        return resp.text or ""
    finally:
        os.remove(tmp)


def synthesize_speech(text: str) -> Optional[bytes]:
    """TTS. Se TTS_PROVIDER='android', o app cuida da fala (retorna None)."""
    if TTS_PROVIDER == "android":
        return None
    if TTS_PROVIDER == "openai" and OPENAI_TTS_API_KEY:
        from openai import OpenAI
        c = OpenAI(api_key=OPENAI_TTS_API_KEY)
        resp = c.audio.speech.create(model="tts-1", voice="nova", input=text)
        return resp.content
    # Piper ou outros: implementar depois. Por ora, None.
    return None
