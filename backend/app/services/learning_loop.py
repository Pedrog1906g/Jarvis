"""Loop de aprendizado contínuo do NEXUS.

A cada 7 dias, destila UMA lição útil a partir dos fatos recentes do dono e registra como
aprendizado no vault do Obsidian (via obsidian.add_learning). É o "ensino contínuo": o
NEXUS mantém o cérebro crescendo mesmo quando o mentor (agente) não está online.
"""
import time
import threading

from app.db.database import SessionLocal
from app.db import models
from app.core.llm import complete_chat
from app.api.agent import _extract_json
from app.services import obsidian

_INTERVAL = 7 * 24 * 3600  # 7 dias


def _recent_facts(n: int = 15):
    db = SessionLocal()
    try:
        facts = (
            db.query(models.MemoryFact)
            .order_by(models.MemoryFact.id.desc())
            .limit(n)
            .all()
        )
        return [f.fact for f in facts]
    finally:
        db.close()


def generate_learning() -> bool:
    facts = _recent_facts()
    facts_block = "\n".join(f"- {f}" for f in facts) or "(sem fatos ainda)"
    prompt = [
        {"role": "system", "content":
         "Você é o mentor do NEXUS AI. Com base nos fatos do dono e no projeto, destile UMA única "
         "lição ou regra ÚTIL e NÃO-ÓBVIA para o NEXUS 'aprender'. Responda SOMENTE em JSON: "
         '{"title":"...","content":"..."}. Se não houver nada novo útil, retorne {"title":"","content":""}.'},
        {"role": "user", "content": f"Fatos recentes do dono:\n{facts_block}"}
    ]
    try:
        raw = complete_chat(prompt, temperature=0.4)
        d = _extract_json(raw)
        if not d or not d.get("title") or not d.get("content"):
            return False
        existing = obsidian.read_note(
            f"{obsidian.VAULT}/13 - Aprendizados (Learnings).md"
        ) or ""
        if d["title"].lower() in existing.lower():
            return False
        return obsidian.add_learning(d["title"], d["content"])
    except Exception as e:
        print("[NEXUS] erro no learning_loop:", e)
        return False


def start_learning_loop():
    def _loop():
        while True:
            try:
                generate_learning()
            except Exception as e:
                print("[NEXUS] learning_loop:", e)
            time.sleep(_INTERVAL)

    threading.Thread(target=_loop, daemon=True).start()
