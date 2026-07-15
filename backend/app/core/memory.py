from typing import List, Dict
from sqlalchemy.orm import Session
from app.db import models
from app.core.llm import complete_chat
from app.core.firebase import mirror_memory
from app.core.personality import JARVIS_SYSTEM_PROMPT

SHORT_TERM_LIMIT = 20  # últimas mensagens consideradas no contexto imediato


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
    # Recuperação simples por sobreposição de palavras (placeholder até vetor DB).
    q_words = set(query.lower().split())
    scored = []
    for f in facts:
        f_words = set(f.fact.lower().split())
        score = len(q_words & f_words) + f.importance
        scored.append((score, f.fact))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [fact for _, fact in scored[:limit]]


def build_messages(db: Session, owner_id: int, conversation_id: int, user_text: str) -> List[Dict[str, str]]:
    history = get_short_term(db, conversation_id)
    facts = get_long_term(db, owner_id, user_text)
    system = JARVIS_SYSTEM_PROMPT
    if facts:
        facts_block = "\n".join(f"- {f}" for f in facts)
        system += f"\n\nMEMÓRIA DE LONGO PRAZO (lembre-se destas preferências/fatos do usuário):\n{facts_block}"
    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})
    return messages


def extract_facts(db: Session, owner_id: int, user_text: str):
    """Extrai fatos duráveis da mensagem do usuário (ex.: 'minha comida favorita é pizza')."""
    if not user_text.strip():
        return
    prompt = [
        {"role": "system", "content":
         "Extraia apenas fatos duráveis e úteis sobre o usuário (preferências, rotina, dados autorizados). "
         "Responda SOMENTE em JSON: {\"facts\": [{\"fact\": \"...\", \"category\": \"...\", \"importance\": 1}]}. "
         "Se não houver fatos, retorne {\"facts\": []}."},
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
            if fact and fact not in existing:
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
            # Sincroniza com o Supabase (cross-device), se configurado.
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
        # Espelha a memória de longo prazo no Firestore (best-effort).
        try:
            facts = db.query(models.MemoryFact).filter(
                models.MemoryFact.owner_id == owner_id).all()
            mirror_memory(owner_id, [f.fact for f in facts])
        except Exception:
            pass
    except Exception:
        db.rollback()
