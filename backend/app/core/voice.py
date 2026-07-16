"""Módulo de voz do NEXUS AI — STT (Whisper via Groq) e TTS.

Provedores TTS suportados:
  - android  (padrão): o app Android usa TTS nativo do dispositivo; backend retorna None.
  - openai: usa a OpenAI TTS API (tts-1, voz 'onyx' — masculina, natural em PT-BR).
  - piper: TTS offline de alta qualidade via binário piper ou pacote piper-tts.
             Requer PIPER_MODEL_PATH e o binário `piper` no PATH (ou pip install piper-tts).

Para o HUD web:
  - Se TTS_PROVIDER=openai/piper → backend sintetiza e o frontend toca via <audio>.
  - Se TTS_PROVIDER=android       → frontend usa Web Speech API do navegador.
"""
import os
import logging
import struct
import subprocess
import tempfile
import wave
from typing import Optional

from app.config import (
    GROQ_API_KEY, GROQ_BASE_URL, GROQ_STT_MODEL,
    TTS_PROVIDER, OPENAI_TTS_API_KEY,
    PIPER_MODEL_PATH, PIPER_EXECUTABLE,
    DEMO_MODE,
)

logger = logging.getLogger("nexus.voice")

# ── Cliente STT (Whisper via Groq) ───────────────────────────────────────────

_stt_client = None
if GROQ_API_KEY:
    from openai import OpenAI
    _stt_client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


# ── Verificação do Piper na inicialização ────────────────────────────────────

_piper_available: Optional[bool] = None


def _check_piper() -> bool:
    global _piper_available
    if _piper_available is not None:
        return _piper_available
    # Tenta o executável configurado ou o padrão "piper"
    exe = PIPER_EXECUTABLE or "piper"
    try:
        result = subprocess.run([exe, "--help"], capture_output=True, timeout=5)
        _piper_available = True
        logger.info("Piper TTS disponível: %s", exe)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Tenta o pacote Python piper-tts
    try:
        from piper import PiperVoice  # type: ignore
        _piper_available = True
        logger.info("Piper TTS disponível via pacote Python (piper-tts).")
        return True
    except ImportError:
        pass
    _piper_available = False
    logger.warning(
        "Piper TTS não encontrado. Instale o binário `piper` ou `pip install piper-tts`. "
        "Configure TTS_PROVIDER=openai para TTS na web sem piper."
    )
    return False


# ── STT ──────────────────────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcrição via Whisper na Groq. Em DEMO_MODE retorna placeholder."""
    if DEMO_MODE or _stt_client is None:
        return "[DEMO] Áudio recebido — configure GROQ_API_KEY para transcrição real em PT-BR."
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


# ── TTS ───────────────────────────────────────────────────────────────────────

def synthesize_speech(text: str) -> Optional[bytes]:
    """Sintetiza texto em áudio. Retorna bytes de áudio ou None.

    - None + status 204 → o cliente usa sua própria síntese (Web Speech API / TTS Android).
    - bytes              → o cliente toca o áudio recebido.
    """
    if not text or not text.strip():
        return None

    # ── Android: TTS nativo no app; HUD usa Web Speech API ──────────────────
    if TTS_PROVIDER == "android":
        return None

    # ── OpenAI TTS ───────────────────────────────────────────────────────────
    if TTS_PROVIDER == "openai":
        if not OPENAI_TTS_API_KEY:
            logger.warning("TTS_PROVIDER=openai mas OPENAI_TTS_API_KEY não está definido.")
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_TTS_API_KEY)
            # 'onyx' = voz masculina, profunda e natural. Excelente em PT-BR.
            resp = client.audio.speech.create(
                model="tts-1-hd",
                voice="onyx",
                input=text,
                response_format="mp3",
            )
            return resp.content
        except Exception as e:
            logger.error("OpenAI TTS falhou: %s", e)
            return None

    # ── Piper TTS (offline, alta qualidade) ──────────────────────────────────
    if TTS_PROVIDER == "piper":
        if not _check_piper():
            return None
        if not PIPER_MODEL_PATH:
            logger.warning("TTS_PROVIDER=piper mas PIPER_MODEL_PATH não está definido.")
            return None

        # Tenta via binário (subprocess)
        exe = PIPER_EXECUTABLE or "piper"
        try:
            result = subprocess.run(
                [exe, "--model", PIPER_MODEL_PATH, "--output-raw"],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                # Piper retorna PCM raw 16-bit; encapsula em WAV
                raw = result.stdout
                return _pcm_to_wav(raw, sample_rate=22050)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning("Piper binário falhou: %s. Tentando pacote Python...", e)

        # Tenta via pacote Python piper-tts
        try:
            from piper import PiperVoice  # type: ignore
            import io
            voice = PiperVoice.load(PIPER_MODEL_PATH)
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav_file:
                voice.synthesize(text, wav_file)
            return buf.getvalue()
        except Exception as e:
            logger.error("Piper Python falhou: %s", e)
            return None

    logger.warning("TTS_PROVIDER='%s' desconhecido. Use: android | openai | piper.", TTS_PROVIDER)
    return None


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 22050, channels: int = 1, bit_depth: int = 16) -> bytes:
    """Encapsula PCM raw em WAV (RIFF header)."""
    data_size = len(pcm_data)
    byte_rate = sample_rate * channels * bit_depth // 8
    block_align = channels * bit_depth // 8
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,           # chunk size
        1,            # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bit_depth,
        b"data",
        data_size,
    )
    return header + pcm_data


def tts_provider_info() -> dict:
    """Retorna informações sobre o provedor TTS ativo (para exibição no frontend)."""
    if TTS_PROVIDER == "android":
        return {"provider": "android", "available": True, "note": "TTS nativo do dispositivo"}
    if TTS_PROVIDER == "openai":
        ok = bool(OPENAI_TTS_API_KEY)
        return {"provider": "openai", "available": ok, "voice": "onyx (masculina)",
                "note": "Alta qualidade, requer API key" if ok else "OPENAI_TTS_API_KEY não definido"}
    if TTS_PROVIDER == "piper":
        ok = _check_piper() and bool(PIPER_MODEL_PATH)
        return {"provider": "piper", "available": ok,
                "model": PIPER_MODEL_PATH or "(não definido)",
                "note": "TTS offline de alta qualidade" if ok else "Binário piper ou PIPER_MODEL_PATH não configurado"}
    return {"provider": TTS_PROVIDER, "available": False, "note": "Provedor desconhecido"}
