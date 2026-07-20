"""
Busca na internet via DuckDuckGo — sem chave de API.
Dá ao JARVIS acesso a informações em tempo real.

Comportamento (pedido do dono): o JARVIS faz SEMPRE uma verificação na internet
para responder com o máximo de precisão possível. A busca é disparada para
qualquer mensagem substantiva (saudações/cortesias curtas são ignoradas).
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

# Saudações / cortesias curtas: não vale a pena buscar na web.
_GREETING_RE = re.compile(
    r'^(oi|olá|ola|oii|oie|e aí|eai|bom dia|boa tarde|boa noite|tudo bem|tudobem|'
    r'bem|obrigad|valeu|vlw|ok|okay|claro|sim|não|nao|kk|rs|haha|opa|fala)\b',
    re.IGNORECASE
)

_STRIP_RE = re.compile(
    r'^(pesquise|busque|google|procure|encontre|me diz|me conte|me fala)\s+'
    r'(sobre|sobre o|sobre a|sobre os|sobre as|sobre um|sobre uma|o que é|quem é|qual é)?\s*',
    re.IGNORECASE
)


_TIME_DATE_RE = re.compile(
    r'\b(que\s+horas|horas?\s+(agora|certas?)|hora\s+atual|'
    r'que\s+dia|dia\s+(de\s+)?hoje|dia\s+atual|data\s+(de\s+)?hoje|data\s+atual|'
    r'qual\s+(o|a)\s+(dia|mes|ano|data)|dia\s+da\s+semana|'
    r'relogio|relógio|'
    r'what\s+time|what\s+day|today\'?s\s+date|current\s+(time|date)|time\s+now)\b',
    re.IGNORECASE
)


def needs_web_search(text: str) -> bool:
    """Verifica se a mensagem deve disparar busca na internet.

    Por padrão, DISPARA para quase toda mensagem substantiva (o dono pediu
    verificação sempre que possível). Apenas saudações/cortesias muito curtas
    são ignoradas para não atrasar respostas triviais. Perguntas de DATA/HORA
    NÃO disparam busca — o backend já injeta o horário exato de Brasília.
    """
    t = (text or "").strip()
    if not t:
        return False
    words = t.split()
    if len(words) <= 3 and _GREETING_RE.match(t):
        return False
    # Perguntas de DATA/HORA: o backend já injeta o horário exato de Brasília
    # no contexto (CONTEXTO TEMPORAL). Buscar na web traz horário cacheado/
    # errado, então ignoramos a busca e usamos o contexto interno.
    if _TIME_DATE_RE.search(t):
        return False
    return True


def extract_query(text: str) -> str:
    """Extrai o termo de busca limpo a partir da mensagem do usuário."""
    clean = _STRIP_RE.sub("", text.strip())
    return clean.strip() or text.strip()


def _search_instant(query: str, max_results: int = 5) -> str:
    """Resposta instantânea do DuckDuckGo (Infobox / definição / resposta direta)."""
    try:
        with httpx.Client(timeout=4, follow_redirects=True) as client:
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
        abstract = (data.get("Abstract") or "").strip()
        if abstract:
            src = data.get("AbstractSource") or data.get("AbstractURL") or ""
            parts.append(f"**{src}**: {abstract}" if src else abstract)
        definition = (data.get("Definition") or "").strip()
        if definition and definition not in abstract:
            src = data.get("DefinitionSource") or ""
            parts.append(f"**{src}**: {definition}" if src else definition)
        answer = (data.get("Answer") or "").strip()
        if answer:
            parts.append(f"Resposta direta: {answer}")
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
        return "\n".join(parts)
    except Exception:
        return ""


def _search_html(query: str, max_results: int = 5) -> str:
    """Fallback: raspa os resultados web (títulos + snippets) do DuckDuckGo HTML."""
    try:
        with httpx.Client(timeout=5, follow_redirects=True) as client:
            r = client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0 Safari/537.36"
                },
            )
            html = r.text

        def _clean(s: str) -> str:
            s = re.sub(r"<[^>]+>", " ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

        parts: list[str] = []
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        for s in snippets:
            c = _clean(s)
            if c:
                parts.append("• " + c[:320])
            if len(parts) >= max_results:
                break
        if not parts:
            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
            for t in titles:
                c = _clean(t)
                if c:
                    parts.append("• " + c[:220])
                if len(parts) >= max_results:
                    break
        return "\n".join(parts)
    except Exception:
        return ""


def search(query: str, max_results: int = 5) -> str:
    """Busca na internet e retorna os resultados como texto formatado.

    Tenta a resposta instantânea; se vier vazia, cai no scrape dos resultados
    web (HTML). Tudo envelopado em try/except para nunca quebrar o chat.
    """
    if not query:
        return ""
    results = _search_instant(query, max_results)
    if not results:
        results = _search_html(query, max_results)
    return results


def format_for_llm(query: str, results: str) -> str:
    """Formata os resultados para injetar como contexto no LLM."""
    if not results:
        return ""
    return (
        f"[BUSCA NA INTERNET — '{query}']\n"
        f"{results}\n"
        f"[FIM DOS RESULTADOS — baseie sua resposta PRIMARIAMENTE nestes dados quando "
        f"eles cobrirem a pergunta do usuário; se não cobrirem, use seu conhecimento. "
        f"Responda de forma natural e concisa, em português do Brasil.]"
    )
