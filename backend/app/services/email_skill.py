"""Habilidade de enviar e-mail por comando de chat.

Se a mensagem for um pedido do tipo "envie um email para fulano@x.com assunto
Oi dizendo Tudo bem", envia o e-mail e retorna a confirmação. Caso contrário,
retorna None (e o chat segue normalmente).
"""

import re

from app.services import email_service as _email


def try_email(content: str):
    c = (content or "").lower()
    if "email" not in c and "e-mail" not in c:
        return None
    m = re.search(r"[\w.\-]+@[\w.\-]+", content)
    if not m:
        return None
    to = m.group(0)

    subject = "Mensagem do NEXUS AI"
    sm = re.search(r"assunto\s+([^\n]{1,80})", content, re.I)
    if sm:
        subject = sm.group(1).strip().rstrip(".!")

    body = ""
    bm = re.search(
        r"(?:dizendo|falando|com\s+o\s+(?:texto|conteúdo|corpo|mensagem)|texto|corpo)\s*[:\-]?\s*(.+)$",
        content, re.I)
    if bm:
        body = bm.group(1).strip()
    if not body:
        body = content  # fallback: usa a própria mensagem

    ok, msg = _email.send_email(to, subject, body)
    if ok:
        return f"✅ E-mail enviado com sucesso para {to} (assunto: {subject})."
    return (f"⚠️ Não consegui enviar o e-mail: {msg}. "
            f"Verifique se o envio de e-mail está configurado no servidor "
            f"(variáveis EMAIL_*).")
