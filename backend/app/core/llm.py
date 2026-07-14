from typing import List, Dict, Iterator
from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL, DEMO_MODE
from app.core.personality import DEMO_PERSONA_LINE

_client = None
if GROQ_API_KEY:
    from openai import OpenAI
    _client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


def stream_chat(messages: List[Dict[str, str]], model: str = GROQ_MODEL) -> Iterator[str]:
    """Gera deltas de texto. Em DEMO_MODE, devolve uma resposta simulada."""
    if DEMO_MODE or _client is None:
        full = _demo_reply(messages)
        for chunk in _chunk_text(full):
            yield chunk
        return

    stream = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def complete_chat(messages: List[Dict[str, str]], model: str = GROQ_MODEL, temperature: float = 0.3) -> str:
    if DEMO_MODE or _client is None:
        return _demo_reply(messages, short=True)

    resp = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=False,
    )
    return resp.choices[0].message.content or ""


def _chunk_text(text: str, size: int = 8):
    # simula streaming caractere a caractere (pequenos pedaços) no modo demo
    for i in range(0, len(text), size):
        yield text[i:i + size]


def _demo_reply(messages: List[Dict[str, str]], short: bool = False) -> str:
    last_user = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last_user = m["content"]
            break
    if short:
        return f"[DEMO] Entendi: '{last_user[:80]}'. Conecte a Groq para respostas reais."
    return (
        f"{DEMO_PERSONA_LINE}\n\n"
        f"Recebi sua mensagem: \"{last_user}\".\n"
        "Como estou em modo de demonstração (sem chave de API), esta é uma resposta simulada. "
        "Conecte sua GROQ_API_KEY no arquivo .env para que eu passe a responder com o modelo real, "
        "com memória, voz e todos os recursos."
    )


def is_available() -> bool:
    return not DEMO_MODE and _client is not None
