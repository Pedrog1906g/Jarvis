from typing import List, Dict
from sqlalchemy.orm import Session
from app.db import models
from app.core.llm import complete_chat
from app.core.firebase import mirror_memory
from app.core.personality import JARVIS_SYSTEM_PROMPT

SHORT_TERM_LIMIT = 20   # últimas mensagens do histórico imediato
SUMMARY_THRESHOLD = 40  # resumir histórico quando passar de N mensagens


def get_short_term(db: Session, conversation_id: int) -> List[Dict[str, str]]:
    msgs = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.id.desc())
        .limit(SHORT_TERM_LIMIT)
        .all()
    )
    msgs.reverse()
    return [{"role": m.role, "content": m.content} for m in msgs]


def get_long_term(db: Session, owner_id: int, query: str = "", limit: int = 8) -> List[str]:
    facts = db.query(models.MemoryFact).filter(models.MemoryFact.owner_id == owner_id).all()
    if not facts:
        return []
    # Recuperação por relevância: combina sobreposição de palavras + importância do fato.
    q_words = set(query.lower().split())
    scored = []
    for f in facts:
        f_words = set(f.fact.lower().split())
        score = len(q_words & f_words) * 2 + f.importance
        scored.append((score, f.fact))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [fact for _, fact in scored[:limit]]


def get_conversation_summary(db: Session, conversation_id: int) -> str:
    """Retorna o resumo comprimido da conversa (se existir)."""
    try:
        row = db.query(models.Setting).filter_by(
            key=f"conv_summary_{conversation_id}").first()
        return row.value if row else ""
    except Exception:
        return ""


def save_conversation_summary(db: Session, conversation_id: int, summary: str):
    """Salva o resumo comprimido da conversa no banco."""
    try:
        row = db.query(models.Setting).filter_by(
            key=f"conv_summary_{conversation_id}").first()
        if row:
            row.value = summary
        else:
            row = models.Setting(key=f"conv_summary_{conversation_id}", value=summary)
            db.add(row)
        db.commit()
    except Exception:
        db.rollback()


def maybe_compress_history(db: Session, owner_id: int, conversation_id: int):
    """
    Comprime o histórico da conversa quando o número de mensagens
    excede SUMMARY_THRESHOLD, salvando um resumo e mantendo apenas as
    últimas SHORT_TERM_LIMIT mensagens para contexto imediato.
    """
    count = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .count()
    )
    if count <= SUMMARY_THRESHOLD:
        return

    # Lê todas as mensagens para gerar um resumo
    all_msgs = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.id)
        .all()
    )
    # Formata para o LLM
    history_text = "\n".join(
        f"{'Usuário' if m.role == 'user' else 'JARVIS'}: {m.content[:300]}"
        for m in all_msgs[:-SHORT_TERM_LIMIT]  # comprime as mais antigas
    )
    prompt = [
        {"role": "system", "content":
         "Você é um assistente de memória. Leia a conversa a seguir e gere um RESUMO COMPACTO "
         "em português, em no máximo 300 palavras, destacando: decisões tomadas, preferências "
         "do usuário, tarefas mencionadas, informações importantes e contexto geral. "
         "Não use listas longas; seja conciso e denso em informação."},
        {"role": "user", "content": f"Conversa para resumir:\n{history_text}"},
    ]
    try:
        summary = complete_chat(prompt, temperature=0.2)
        if summary:
            existing = get_conversation_summary(db, conversation_id)
            if existing:
                # Combina o resumo antigo com o novo
                combined_prompt = [
                    {"role": "system", "content":
                     "Combine os dois resumos de conversa abaixo em um único resumo coerente e compacto (máx. 400 palavras)."},
                    {"role": "user", "content": f"Resumo anterior:\n{existing}\n\nNovo resumo:\n{summary}"},
                ]
                try:
                    summary = complete_chat(combined_prompt, temperature=0.1)
                except Exception:
                    pass
            save_conversation_summary(db, conversation_id, summary)
    except Exception:
        pass


def build_messages(db: Session, owner_id: int, conversation_id: int, user_text: str) -> List[Dict[str, str]]:
    history = get_short_term(db, conversation_id)
    facts = get_long_term(db, owner_id, user_text)
    summary = get_conversation_summary(db, conversation_id)

    system = JARVIS_SYSTEM_PROMPT

    # Contexto temporal — JARVIS sabe o dia/hora/fuso atual
    import datetime
    _now = datetime.datetime.now()
    _weekdays_pt = ["segunda-feira", "terça-feira", "quarta-feira",
                    "quinta-feira", "sexta-feira", "sábado", "domingo"]
    _weekday = _weekdays_pt[_now.weekday()]
    system += (
        f"\n\nCONTEXTO TEMPORAL (atualizado a cada mensagem):\n"
        f"Data: {_now.strftime('%d/%m/%Y')} ({_weekday}) | "
        f"Hora: {_now.strftime('%H:%M')} (UTC) | "
        f"Use para saudações e respostas sobre data/hora."
    )

    # Injeta memória de longo prazo (fatos)
    if facts:
        facts_block = "\n".join(f"- {f}" for f in facts)
        system += f"\n\nMEMÓRIA DE LONGO PRAZO (use quando relevante):\n{facts_block}"

    # Injeta resumo da conversa anterior (contexto comprimido)
    if summary:
        system += f"\n\nRESUMO DA CONVERSA ANTERIOR:\n{summary}"

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})
    return messages


def extract_facts(db: Session, owner_id: int, user_text: str):
    """Extrai fatos duráveis da mensagem do usuário e os armazena na memória de longo prazo."""
    if not user_text.strip():
        return
    prompt = [
        {"role": "system", "content":
         "Extraia apenas fatos duráveis e úteis sobre o usuário (preferências, rotina, dados autorizados, "
         "objetivos de longo prazo, habilidades, localização se mencionada). "
         "Responda SOMENTE em JSON: {\"facts\": [{\"fact\": \"...\", \"category\": \"...\", \"importance\": 1}]}. "
         "Se não houver fatos, retorne {\"facts\": []}. "
         "Exemplos de fato: 'Prefere café sem açúcar', 'Trabalha como designer gráfico', 'Mora em São Paulo'. "
         "NÃO extraia fatos triviais ou de curto prazo como 'perguntou que horas são'."},
        {"role": "user", "content": user_text},
    ]
    try:
        raw = complete_chat(prompt, temperature=0.1)
        import json, re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return
        data = json.loads(m.group(0))
        existing = {
            f.fact
            for f in db.query(models.MemoryFact)
            .filter(models.MemoryFact.owner_id == owner_id).all()
        }
        new_facts = []
        for item in data.get("facts", []):
            fact = item.get("fact")
            if fact and fact not in existing and len(fact) > 10:
                cat = item.get("category", "geral")
                imp = int(item.get("importance", 1))
                db.add(models.MemoryFact(
                    owner_id=owner_id,
                    fact=fact,
                    category=cat,
                    importance=imp,
                ))
                existing.add(fact)
                new_facts.append((fact, cat, imp))
        if new_facts:
            db.commit()
            # Sincroniza com Firebase (best-effort)
            try:
                facts_all = db.query(models.MemoryFact).filter(
                    models.MemoryFact.owner_id == owner_id).all()
                mirror_memory(owner_id, [f.fact for f in facts_all])
            except Exception:
                pass
            # Sincroniza com Supabase (best-effort)
            try:
                from app.services import supabase_sync
                if supabase_sync.sc.is_configured():
                    uname = db.query(models.User).filter(
                        models.User.id == owner_id).first()
                    uname = uname.username if uname else "owner"
                    for f, c, i in new_facts:
                        supabase_sync.sync_memory(uname, f, c, i)
            except Exception:
                pass
        else:
            db.rollback()
    except Exception:
        db.rollback()
