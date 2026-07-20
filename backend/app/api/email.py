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


class EmailConfigRequest(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    address: str = ""
    password: str = ""
    use_ssl: bool = False
    from_name: str = "NEXUS AI"


@router.post("/send")
def send(req: EmailRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode enviar e-mails"}
    ok, msg = _email.send_email(req.to, req.subject, req.body)
    return {"status": "ok" if ok else "error", "message": msg}


@router.post("/set_config")
def set_config(req: EmailConfigRequest, user: models.User = Depends(get_current_user)):
    """Salva a config de SMTP no banco (senha criptografada) e aplica na hora."""
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode configurar o e-mail"}
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import encrypt
        db = SessionLocal()
        try:
            def _set(key, val, secret=False):
                val = (val or "")
                if secret and val:
                    val = encrypt(val)
                row = db.query(models.Setting).filter_by(key=key).first()
                if val:
                    if row:
                        row.value = val
                    else:
                        db.add(models.Setting(key=key, value=val))
                elif row:
                    db.delete(row)

            _set("EMAIL_SMTP_HOST", req.smtp_host)
            _set("EMAIL_SMTP_PORT", str(req.smtp_port))
            _set("EMAIL_ADDRESS", req.address)
            _set("EMAIL_PASSWORD", req.password, secret=True)
            _set("EMAIL_SMTP_SSL", "true" if req.use_ssl else "false")
            _set("EMAIL_FROM_NAME", req.from_name or "NEXUS AI")
            db.commit()
        finally:
            db.close()

        # Aplica imediatamente na memória/ambiente (funciona na hora, sem reiniciar)
        _email.set_runtime("EMAIL_SMTP_HOST", req.smtp_host)
        _email.set_runtime("EMAIL_SMTP_PORT", str(req.smtp_port))
        _email.set_runtime("EMAIL_ADDRESS", req.address)
        _email.set_runtime("EMAIL_PASSWORD", req.password)
        _email.set_runtime("EMAIL_SMTP_SSL", "true" if req.use_ssl else "false")
        _email.set_runtime("EMAIL_FROM_NAME", req.from_name or "NEXUS AI")
        return {"status": "ok",
                "message": "E-mail configurado. Agora você pode enviar e-mails pelo JARVIS."}
    except Exception as e:
        return {"status": "error", "message": f"erro ao salvar: {e}"}


@router.get("/config")
def get_config(user: models.User = Depends(get_current_user)):
    """Mostra o status da config (sem expor a senha)."""
    return {
        "configured": _email.is_configured(),
        "smtp_host": _email.get_cfg("EMAIL_SMTP_HOST"),
        "smtp_port": _email.get_cfg("EMAIL_SMTP_PORT", "587"),
        "address": _email.get_cfg("EMAIL_ADDRESS"),
        "has_password": bool(_email.get_cfg("EMAIL_PASSWORD")),
        "use_ssl": _email.get_cfg("EMAIL_SMTP_SSL", "false"),
        "from_name": _email.get_cfg("EMAIL_FROM_NAME", "NEXUS AI"),
    }


@router.post("/test")
def test_email(user: models.User = Depends(get_current_user)):
    """Envia um e-mail de teste para o próprio endereço configurado."""
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode testar o e-mail"}
    addr = _email.get_cfg("EMAIL_ADDRESS")
    if not addr:
        return {"status": "error", "message": "e-mail não configurado"}
    ok, msg = _email.send_email(
        addr,
        "Teste do NEXUS AI",
        "Este é um e-mail de teste enviado pelo JARVIS. Se você recebeu, está funcionando!",
    )
    return {"status": "ok" if ok else "error", "message": msg}
