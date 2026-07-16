import json
from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user, ws_user
from app.core.llm import stream_chat, complete_chat, is_available
from app.core.memory import build_messages, extract_facts, maybe_compress_history
from app.core import web_search as _ws
from app.core.firebase import mirror_user, mirror_message
from app.core.ws_manager import manager
from app.services import obsidian as _obs

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    content: str
    conversation_id: Optional[int] = None


def _sync_msg(owner_username: str, conversation_id, role: str, content: str):
    """Espelha a mensagem no Supabase (cross-device). No-op se não configurado."""
    try:
        from app.services import supabase_sync
        if supabase_sync.sc.is_configured():
            supabase_sync.sync_message(owner_username, conversation_id, role, content)
    except Exception:
        pass


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db),
         user: models.User = Depends(get_current_user)):
    """Endpoint não-streaming (útil para testes via curl/Postman)."""
    conv = _get_or_create_conversation(db, user.id, req.conversation_id)
    db.add(models.Message(conversation_id=conv.id, role="user", content=req.content))
    db.commit()
    _sync_msg(user.username, conv.id, "user", req.content)
    extract_facts(db, user.id, req.content)

    messages = build_messages(db, user.id, conv.id, req.content)
    _vctx = _obs.chat_context_message()
    if _vctx:
        messages.insert(1, _vctx)
    # Busca na internet (endpoint REST síncrono)
    if _ws.needs_web_search(req.content):
        try:
            query = _ws.extract_query(req.content)
            results = _ws.search(query)
            if results:
                messages.insert(-1, {"role": "system", "content": _ws.format_for_llm(query, results)})
        except Exception:
            pass
    reply = "".join(stream_chat(messages))
    db.add(models.Message(conversation_id=conv.id, role="assistant", content=reply))
    db.commit()
    _sync_msg(user.username, conv.id, "assistant", reply)
    _auto_title(db, user.id, conv)
    # Espelha no Firestore (best-effort) quando o Firebase está ativo.
    try:
        mirror_user(user)
        last_user = db.query(models.Message).filter_by(
            conversation_id=conv.id, role="user").order_by(models.Message.id.desc()).first()
        last_asst = db.query(models.Message).filter_by(
            conversation_id=conv.id, role="assistant").order_by(models.Message.id.desc()).first()
        if last_user:
            mirror_message(conv.id, last_user)
        if last_asst:
            mirror_message(conv.id, last_asst)
    except Exception:
        pass
    return {"conversation_id": conv.id, "reply": reply, "demo": not is_available()}


@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    convs = db.query(models.Conversation).filter(
        models.Conversation.owner_id == user.id).order_by(models.Conversation.updated_at.desc()).all()
    result = []
    for c in convs:
        last = db.query(models.Message).filter(
            models.Message.conversation_id == c.id).order_by(models.Message.id.desc()).first()
        result.append({
            "id": c.id, "title": c.title,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "preview": last.content[:80] if last else "",
        })
    return result


@router.get("/conversations/{cid}/messages")
def conversation_messages(cid: int, db: Session = Depends(get_db),
                          user: models.User = Depends(get_current_user)):
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == cid, models.Conversation.owner_id == user.id).first()
    if not conv:
        return []
    msgs = db.query(models.Message).filter(
        models.Message.conversation_id == cid).order_by(models.Message.id).all()
    return [{"id": m.id, "role": m.role, "content": m.content} for m in msgs]


@router.delete("/conversations/{cid}")
def delete_conversation(cid: int, db: Session = Depends(get_db),
                        user: models.User = Depends(get_current_user)):
    """Apaga uma conversa e todas as suas mensagens."""
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == cid, models.Conversation.owner_id == user.id).first()
    if not conv:
        return {"ok": False, "message": "Conversa não encontrada"}
    db.delete(conv)
    db.commit()
    return {"ok": True}


def _auto_title(db: Session, owner_id: int, conv: models.Conversation):
    """Gera título automático da conversa após a 3ª mensagem (best-effort, via LLM)."""
    if conv.title != "Conversa":
        return  # Já tem título personalizado
    count = db.query(models.Message).filter_by(conversation_id=conv.id).count()
    if count != 3:
        return  # Gera o título apenas na 3ª mensagem
    import threading
    def _gen():
        try:
            from app.db.database import SessionLocal
            s = SessionLocal()
            try:
                msgs = s.query(models.Message).filter_by(conversation_id=conv.id).order_by(
                    models.Message.id).limit(3).all()
                snippet = " | ".join(m.content[:80] for m in msgs)
                prompt = [
                    {"role": "system", "content":
                     "Gere um TÍTULO CURTO (máx 5 palavras, sem aspas) para esta conversa. "
                     "Responda APENAS o título, nada mais."},
                    {"role": "user", "content": snippet},
                ]
                title = complete_chat(prompt, temperature=0.3).strip().strip('"\'').strip()
                if title and len(title) <= 60:
                    c = s.query(models.Conversation).filter_by(id=conv.id).first()
                    if c and c.title == "Conversa":
                        c.title = title
                        s.commit()
            finally:
                s.close()
        except Exception:
            pass
    threading.Thread(target=_gen, daemon=True).start()


def _get_or_create_conversation(db, owner_id, conversation_id):
    if conversation_id:
        conv = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id,
            models.Conversation.owner_id == owner_id,
        ).first()
        if conv:
            return conv
    conv = models.Conversation(owner_id=owner_id, title="Conversa")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket, token: str = ""):
    await websocket.accept()
    db = next(get_db())
    user = ws_user(token, db)
    if not user:
        await websocket.send_json({"type": "error", "message": "Não autenticado"})
        await websocket.close()
        return

    manager.connect(user.id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") != "message":
                continue
            content = data.get("content", "")
            conversation_id = data.get("conversation_id")
            conv = _get_or_create_conversation(db, user.id, conversation_id)
            db.add(models.Message(conversation_id=conv.id, role="user", content=content))
            db.commit()
            _sync_msg(user.username, conv.id, "user", content)
            extract_facts(db, user.id, content)

            # Gatilho de auto-melhoria via chat (somente o dono).
            if user.username == "owner":
                from app.api import agent as _agent
                if _agent.detect_self_improve(content):
                    _agent.trigger_self_improve(content)
                    await websocket.send_json({"type": "start", "conversation_id": conv.id})
                    await websocket.send_json({
                        "type": "delta",
                        "content": "⚙️ Auto-melhoria iniciada em segundo plano. Vou analisar e melhorar meu "
                                   "código, com backup automático. Pergunte 'status da auto-melhoria' para acompanhar.",
                    })
                    await websocket.send_json({"type": "done", "conversation_id": conv.id})
                    continue

            messages = build_messages(db, user.id, conv.id, content)
            _vctx = _obs.chat_context_message()
            if _vctx:
                messages.insert(1, _vctx)

            # Busca na internet quando o usuário pede informações em tempo real
            if _ws.needs_web_search(content):
                try:
                    import asyncio
                    query = _ws.extract_query(content)
                    results = await asyncio.to_thread(_ws.search, query)
                    if results:
                        ctx = _ws.format_for_llm(query, results)
                        messages.insert(-1, {"role": "system", "content": ctx})
                except Exception:
                    pass

            await websocket.send_json({"type": "start", "conversation_id": conv.id})
            full = []
            for delta in stream_chat(messages):
                full.append(delta)
                await websocket.send_json({"type": "delta", "content": delta})
            reply = "".join(full)
            db.add(models.Message(conversation_id=conv.id, role="assistant", content=reply))
            db.commit()
            _sync_msg(user.username, conv.id, "assistant", reply)
            # Comprime histórico se ficou muito longo (best-effort, em background)
            try:
                import threading
                threading.Thread(
                    target=maybe_compress_history,
                    args=(next(get_db()), user.id, conv.id),
                    daemon=True
                ).start()
            except Exception:
                pass
            await websocket.send_json({"type": "done", "conversation_id": conv.id})
            _auto_title(db, user.id, conv)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user.id, websocket)
        db.close()
