"""
Busca na internet via DuckDuckGo — sem chave de API.
Dá ao JARVIS acesso a informações em tempo real.
"""
import re
import httpx

_NEEDS_SEARCH_RE = re.compile(
    r'\b(pesquise|busque|google|procure|encontre|pesquisar|buscar|me diz|me conte|me fala|'
    r'o que é|quem é|qual é|quando foi|quando é|onde fica|onde é|quantos|quanto custa|'
    r'como funciona|como se faz|o que aconteceu|notícias|novidades|últimas notícias|'
    r'preço|cotação|temperatura|clima hoje|clima em|previsão do tempo|câmbio|'
    r'dólar|euro|bitcoin|ethereum|cripto|criptomoeda|resultado|placar|score|'
    r'quem ganhou|quem venceu|última hora|acontecendo|lançamento|estreia|'
    r'quem é o presidente|quem é o dono|qual a capital|qual a população|'
    r'who is|what is|when is|where is|how much|how many|latest|news|search|'
    r'tell me about|explain|define|definition|meaning|translate)\b',
    re.IGNORECASE
)

_STRIP_RE = re.compile(
    r'^(pesquise|busque|google|procure|encontre|me diz|me conte|me fala)\s+'
    r'(sobre|sobre o|sobre a|sobre os|sobre as|sobre um|sobre uma|o que é|quem é|qual é)?\s*',
    re.IGNORECASE
)


def needs_web_search(text: str) -> bool:
    """Verifica se a mensagem provavelmente precisa de busca na internet."""
    return bool(_NEEDS_SEARCH_RE.search(text))


def extract_query(text: str) -> str:
    """Extrai o termo de busca limpo a partir da mensagem do usuário."""
    clean = _STRIP_RE.sub("", text.strip())
    return clean.strip() or text.strip()


def search(query: str, max_results: int = 5) -> str:
    """
    Busca no DuckDuckGo e retorna os resultados como texto formatado.
    Usa a Instant Answer API (sem chave) + resultados relacionados.
    """
    try:
        with httpx.Client(timeout=7, follow_redirects=True) as client:
            r = client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1",
                    "kl": "br-pt",
                },
                headers={"User-Agent": "JARVIS-NEXUS/1.0 (personal assistant)"},
            )
            data = r.json()

        parts: list[str] = []

        # Resposta instantânea (Infobox / Wikipedia etc.)
        abstract = (data.get("Abstract") or "").strip()
        if abstract:
            src = data.get("AbstractSource") or data.get("AbstractURL") or ""
            parts.append(f"**{src}**: {abstract}" if src else abstract)

        # Definição (Glossário)
        definition = (data.get("Definition") or "").strip()
        if definition and definition not in abstract:
            src = data.get("DefinitionSource") or ""
            parts.append(f"**{src}**: {definition}" if src else definition)

        # Resposta direta (ex.: resultados matemáticos, conversões)
        answer = (data.get("Answer") or "").strip()
        if answer:
            parts.append(f"Resposta direta: {answer}")

        # Tópicos relacionados
        for topic in data.get("RelatedTopics", []):
            if len(parts) >= max_results + 1:
                break
            if isinstance(topic, dict) and topic.get("Text"):
                txt = topic["Text"][:300].strip()
                if txt:
                    parts.append(f"• {txt}")
            elif isinstance(topic, dict) and topic.get("Topics"):
                for sub in topic["Topics"]:
                    if len(parts) >= max_results + 1:
                        break
                    if isinstance(sub, dict) and sub.get("Text"):
                        parts.append(f"• {sub['Text'][:300].strip()}")

        return "\n".join(parts) if parts else ""

    except Exception:
        return ""


def format_for_llm(query: str, results: str) -> str:
    """Formata os resultados para injetar como contexto no LLM."""
    if not results:
        return ""
    return (
        f"[BUSCA NA INTERNET — '{query}']\n"
        f"{results}\n"
        f"[FIM DOS RESULTADOS — responda ao usuário usando essas informações de forma natural e concisa]"
    )
