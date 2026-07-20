"""Envio de e-mails pelo NEXUS AI / JARVIS (SMTP).

Ordem de prioridade da configuração:
  1. Configuração salva em tempo de execução (via /api/email/set_config ou banco).
  2. Variáveis de ambiente (EMAIL_SMTP_HOST, EMAIL_ADDRESS, ...).

Ativa quando houver EMAIL_ADDRESS + EMAIL_SMTP_HOST. Sem isso, `send_email`
retorna (False, "não configurado") e o resto do sistema segue normalmente.
"""

import os
import logging
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("nexus.email")

# Cache de configuração em tempo de execução (prioridade sobre as env vars).
_RT = {}


def set_runtime(key: str, value: str):
    """Define uma config de e-mail em tempo de execução (e no ambiente)."""
    key = str(key).upper()
    _RT[key] = value or ""
    os.environ[key] = value or ""


def get_cfg(key: str, default: str = "") -> str:
    """Lê a config: primeiro o cache de runtime, depois a env var."""
    return _RT.get(key) or os.getenv(key, default)


def is_configured() -> bool:
    return bool(get_cfg("EMAIL_ADDRESS") and get_cfg("EMAIL_SMTP_HOST"))


def send_email(to: str, subject: str, body: str):
    """Envia um e-mail via SMTP. Retorna (ok: bool, mensagem: str)."""
    host = get_cfg("EMAIL_SMTP_HOST")
    addr = get_cfg("EMAIL_ADDRESS")
    pwd = get_cfg("EMAIL_PASSWORD", "")
    port = int(get_cfg("EMAIL_SMTP_PORT", "587") or "587")
    from_name = get_cfg("EMAIL_FROM_NAME", "NEXUS AI")
    use_ssl = get_cfg("EMAIL_SMTP_SSL", "false").lower() in ("1", "true", "yes", "on")

    if not (host and addr):
        return False, ("e-mail não configurado (use /api/email/set_config "
                       "ou defina as variáveis EMAIL_* no servidor)")

    try:
        msg = EmailMessage()
        msg["From"] = f"{from_name} <{addr}>"
        msg["To"] = to
        msg["Subject"] = subject or "Mensagem do NEXUS AI"
        msg.set_content(body or "")

        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=30) as s:
                if pwd:
                    s.login(addr, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.starttls()
                if pwd:
                    s.login(addr, pwd)
                s.send_message(msg)
        log.info("E-mail enviado para %s", to)
        return True, "ok"
    except Exception as e:
        log.warning("send_email falhou: %s", e)
        return False, str(e)
