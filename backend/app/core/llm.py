from typing import List, Dict, Iterator
from app.config import (
    LLM_PROVIDER,
    GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    GOOGLE_API_KEY, GOOGLE_MODEL,
    DEMO_MODE
)
from app.core.personality import DEMO_PERSONA_LINE

# Clients são construídos sob demanda (lazy) para que chaves configuradas pelo dono
# (via API/banco, criptografadas) tenham prioridade sobre o ambiente e não exijam reinício.
_clients = {}


def _db_key(name: str) -> str:
    """Lê uma chave criptografada do banco (Setting). Retorna '' se ausente."""
    try:
        from app.db.database import SessionLocal
        from app.db import models
        from app.core.crypto import decrypt
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key=name).first()
            return decrypt(row.value) if row and row.value else ""
        finally:
            db.close()
    except Exception:
        return ""


def _effective(env_val: str, db_name: str) -> str:
    # Banco tem prioridade: chave configurada pelo dono no app sobrepõe o ambiente
    # (ex.: quando a chave do ambiente no Render está inválida/expirada).
    return _db_key(db_name) or env_val


def _build_groq():
    from openai import OpenAI
    k = _effective(GROQ_API_KEY, "groq_api_key")
    if k:
        _clients["groq"] = OpenAI(api_key=k, base_url=GROQ_BASE_URL)
    return _clients.get("groq")


def _build_openai():
    from openai import OpenAI
    k = _effective(OPENAI_API_KEY, "openai_api_key")
    if k:
        _clients["openai"] = OpenAI(api_key=k)
    return _clients.get("openai")


# Ollama
try:
    import ollama
    _clients["ollama"] = ollama
except ImportError:
    pass

# Anthropic (ambiente ou banco)
if ANTHROPIC_API_KEY or _db_key("anthropic_api_key"):
    try:
        import anthropic
        _clients["anthropic"] = anthropic.Anthropic(
            api_key=_effective(ANTHROPIC_API_KEY, "anthropic_api_key"))
    except ImportError:
        pass

# Google Gemini (ambiente ou banco)
if GOOGLE_API_KEY or _db_key("google_api_key"):
    try:
        import google.generativeai as genai
        genai.configure(api_key=_effective(GOOGLE_API_KEY, "google_api_key"))
        _clients["google"] = genai
    except ImportError:
        pass


def _client(provider: str):
    """Devolve o cliente sob demanda, construindo-o se necessário (incl. chave do banco)."""
    if provider in _clients:
        return _clients[provider]
    if provider == "groq":
        return _build_groq()
    if provider == "openai":
        return _build_openai()
    return None


def get_current_model() -> str:
    if LLM_PROVIDER == "groq":
        return GROQ_MODEL
    elif LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    elif LLM_PROVIDER == "ollama":
        return OLLAMA_MODEL
    elif LLM_PROVIDER == "anthropic":
        return ANTHROPIC_MODEL
    elif LLM_PROVIDER == "google":
        return GOOGLE_MODEL
    return GROQ_MODEL


def stream_chat(messages: List[Dict[str, str]], model: str = None) -> Iterator[str]:
    """Gera deltas de texto. Em DEMO_MODE, devolve uma resposta simulada."""
    if model is None:
        model = get_current_model()
        
    if DEMO_MODE:
        full = _demo_reply(messages)
        for chunk in _chunk_text(full):
            yield chunk
        return

    if LLM_PROVIDER == "groq":
        client = _client("groq")
        if client:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return

    elif LLM_PROVIDER == "openai" and "openai" in _clients:
        client = _clients["openai"]
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
        return

    elif LLM_PROVIDER == "ollama" and "ollama" in _clients:
        client = _clients["ollama"]
        try:
            stream = client.chat(
                model=model,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
        except Exception:
            # Fallback to demo if Ollama fails
            full = _demo_reply(messages)
            for chunk in _chunk_text(full):
                yield chunk
        return

    elif LLM_PROVIDER == "anthropic" and "anthropic" in _clients:
        client = _clients["anthropic"]
        # Convert messages to Anthropic format (system message separate)
        system_msg = None
        filtered_msgs = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                filtered_msgs.append(msg)
        
        with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system_msg,
            messages=filtered_msgs
        ) as stream:
            for text in stream.text_stream:
                yield text
        return

    elif LLM_PROVIDER == "google" and "google" in _clients:
        genai = _clients["google"]
        # Convert messages to Gemini format
        system_msg = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        model_instance = genai.GenerativeModel(model_name=model)
        chat = model_instance.start_chat(history=contents[:-1])  # All except last user message
        response = chat.send_message(contents[-1]["parts"][0]["text"], stream=True)
        for chunk in response:
            yield chunk.text
        return

    # Fallback to demo
    full = _demo_reply(messages)
    for chunk in _chunk_text(full):
        yield chunk


def complete_chat(messages: List[Dict[str, str]], model: str = None, temperature: float = 0.3) -> str:
    if model is None:
        model = get_current_model()
        
    if DEMO_MODE:
        return _demo_reply(messages, short=True)

    if LLM_PROVIDER == "groq":
        client = _client("groq")
        if client:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return resp.choices[0].message.content or ""

    elif LLM_PROVIDER == "openai" and "openai" in _clients:
        client = _clients["openai"]
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=False,
        )
        return resp.choices[0].message.content or ""

    elif LLM_PROVIDER == "ollama" and "ollama" in _clients:
        client = _clients["ollama"]
        try:
            resp = client.chat(
                model=model,
                messages=messages,
                stream=False
            )
            return resp["message"]["content"]
        except Exception:
            return _demo_reply(messages, short=True)

    elif LLM_PROVIDER == "anthropic" and "anthropic" in _clients:
        client = _clients["anthropic"]
        # Convert messages to Anthropic format
        system_msg = None
        filtered_msgs = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                filtered_msgs.append(msg)
        
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_msg,
            messages=filtered_msgs
        )
        return message.content[0].text

    elif LLM_PROVIDER == "google" and "google" in _clients:
        genai = _clients["google"]
        # Convert messages to Gemini format
        system_msg = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        model_instance = genai.GenerativeModel(model_name=model)
        chat = model_instance.start_chat(history=contents[:-1])
        response = chat.send_message(contents[-1]["parts"][0]["text"])
        return response.text

    return _demo_reply(messages, short=True)


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
        return f"[DEMO] Entendi: '{last_user[:80]}'. Configure uma chave de API para respostas reais."
    return (
        f"{DEMO_PERSONA_LINE}\n\n"
        f"Recebi sua mensagem: \"{last_user}\".\n"
        "Como estou em modo de demonstração (sem chave de API), esta é uma resposta simulada. "
        "Configure uma chave de API no arquivo .env para que eu passe a responder com o modelo real, "
        "com memória, voz e todos os recursos."
    )


def is_available() -> bool:
    if DEMO_MODE:
        return False
    if LLM_PROVIDER == "groq":
        return bool(_client("groq"))
    if LLM_PROVIDER == "openai":
        return bool(_client("openai"))
    return LLM_PROVIDER in _clients
