"""Endpoints de e-mail do NEXUS AI (somente o dono)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import models
from app.core.security import get_current_user
from app.services import email_service as _email

router = APIRouter(prefix="/api/email", tags=["email"])


class EmailRequest(BaseModel):
    to: str
    subject: str = "Mensagem do NEXUS AI"
    body: str


@router.post("/send")
def send(req: EmailRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode enviar e-mails"}
    ok, msg = _email.send_email(req.to, req.subject, req.body)
    return {"status": "ok" if ok else "error", "message": msg}
