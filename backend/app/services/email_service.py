"""Envio de e-mails pelo NEXUS AI / JARVIS (SMTP).

Ativa SOZINHO quando as variáveis EMAIL_SMTP_HOST + EMAIL_ADDRESS estiverem
definidas no servidor (ex.: no painel do Render). Sem elas, `send_email`
retorna (False, "não configurado") e o resto do sistema segue normalmente.
"""

import os
import logging
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("nexus.email")


def is_configured() -> bool:
    return bool(os.getenv("EMAIL_ADDRESS") and os.getenv("EMAIL_SMTP_HOST"))


def send_email(to: str, subject: str, body: str):
    """Envia um e-mail via SMTP. Retorna (ok: bool, mensagem: str)."""
    host = os.getenv("EMAIL_SMTP_HOST")
    addr = os.getenv("EMAIL_ADDRESS")
    pwd = os.getenv("EMAIL_PASSWORD", "")
    port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    from_name = os.getenv("EMAIL_FROM_NAME", "NEXUS AI")
    use_ssl = os.getenv("EMAIL_SMTP_SSL", "false").lower() in ("1", "true", "yes")

    if not (host and addr):
        return False, "e-mail não configurado no servidor (defina EMAIL_SMTP_HOST/EMAIL_ADDRESS/EMAIL_PASSWORD)"

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
