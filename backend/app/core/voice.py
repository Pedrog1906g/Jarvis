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
    """TTS. Retorna bytes de áudio (mp3) ou None.

    Provedores suportados:
      - android (padrão): o app Android cuida da síntese de voz — o backend
        retorna None (204 No Content) e o app usa o TTS nativo do dispositivo.
      - openai: usa a API TTS da OpenAI (tts-1, voz masculina 'echo').
        Requer OPENAI_TTS_API_KEY no .env.
      - piper: provedor offline ainda não integrado neste servidor. Configure
        TTS_PROVIDER=openai para obter TTS real na web.
    """
    if TTS_PROVIDER == "android":
        # Comportamento esperado: o app Android usa TTS nativo (offline, PT-BR).
        # O HUD web usa a Web Speech API do próprio navegador (sem chamada ao backend).
        return None
    if TTS_PROVIDER == "openai" and OPENAI_TTS_API_KEY:
        from openai import OpenAI
        c = OpenAI(api_key=OPENAI_TTS_API_KEY)
        # Voz 'echo' é masculina e natural em PT-BR (melhor opção disponível na API).
        resp = c.audio.speech.create(model="tts-1", voice="echo", input=text)
        return resp.content
    if TTS_PROVIDER == "piper":
        # Piper é um TTS offline de alta qualidade. Para ativá-lo:
        # 1. Instale piper-tts no sistema (pip install piper-tts ou binário).
        # 2. Defina PIPER_MODEL_PATH no .env apontando para o modelo .onnx PT-BR.
        # 3. O backend chamará piper via subprocess e retornará o audio/wav.
        # Por ora, retorna None para não quebrar o fluxo.
        import logging
        logging.getLogger("nexus.voice").warning(
            "TTS_PROVIDER=piper configurado mas piper não está integrado neste servidor. "
            "Configure TTS_PROVIDER=openai com OPENAI_TTS_API_KEY para TTS real via web."
        )
        return None
    return None
