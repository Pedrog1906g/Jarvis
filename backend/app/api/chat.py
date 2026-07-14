import json
from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user, ws_user
from app.core.llm import stream_chat, is_available
from app.core.memory import build_messages, extract_facts

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    content: str
    conversation_id: Optional[int] = None


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db),
         user: models.User = Depends(get_current_user)):
    """Endpoint não-streaming (útil para testes via curl/Postman)."""
    conv = _get_or_create_conversation(db, user.id, req.conversation_id)
    db.add(models.Message(conversation_id=conv.id, role="user", content=req.content))
    db.commit()
    extract_facts(db, user.id, req.content)

    messages = build_messages(db, user.id, conv.id, req.content)
    reply = "".join(stream_chat(messages))
    db.add(models.Message(conversation_id=conv.id, role="assistant", content=reply))
    db.commit()
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
            extract_facts(db, user.id, content)

            messages = build_messages(db, user.id, conv.id, content)
            await websocket.send_json({"type": "start", "conversation_id": conv.id})
            full = []
            for delta in stream_chat(messages):
                full.append(delta)
                await websocket.send_json({"type": "delta", "content": delta})
            reply = "".join(full)
            db.add(models.Message(conversation_id=conv.id, role="assistant", content=reply))
            db.commit()
            await websocket.send_json({"type": "done", "conversation_id": conv.id})
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
