"""Bot do Telegram para o NEXUS AI / JARVIS.

Ativa SOZINHO quando a variável de ambiente TELEGRAM_BOT_TOKEN estiver
definida (no Render / servidor). Quando ativo, o JARVIS responde no Telegram
exatamente como no chat: entende português, busca na internet, usa memória e
segundo cérebro, e ainda envia e-mails ("envie um email para fulano@x.com ...").

Como funciona:
  - Faz long-polling de /getUpdates da API do Telegram.
  - Cada mensagem do dono vira uma chamada ao próprio /api/chat do backend
    (reaproveitando TODA a inteligência já existente, sem duplicar código).
  - Se a mensagem for um pedido de e-mail, dispara o serviço de e-mail.
"""

import os
import logging
import threading
import time

import httpx

from app.services import email_skill

log = logging.getLogger("nexus.telegram")

_POLL = "https://api.telegram.org/bot{}/"
_DEFAULT_BASE = "https://nexus-api-2o1y.onrender.com"


def _token() -> str:
    return (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()


def _public_base() -> str:
    return (os.getenv("PUBLIC_BASE_URL") or _DEFAULT_BASE).rstrip("/")


def _owner_token(base: str):
    """Faz login como dono para obter o JWT usado nas chamadas ao /api/chat."""
    try:
        r = httpx.post(
            base + "/api/auth/login",
            json={"username": "owner",
                  "passphrase": os.getenv("OWNER_PASSPHRASE", "nexus")},
            timeout=20,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
    except Exception as e:
        log.warning("Telegram: falhou login do dono: %s", e)
    return None


def _answer(base: str, owner_tok: str, text: str) -> str:
    """Responde à mensagem: e-mail se for o caso, senão o chat normal."""
    email_reply = email_skill.try_email(text)
    if email_reply is not None:
        return email_reply
    try:
        r = httpx.post(
            base + "/api/chat",
            headers={"Authorization": "Bearer " + owner_tok},
            json={"content": text, "conversation_id": None},
            timeout=60,
        )
        if r.status_code == 200:
            return (r.json().get("reply") or "").strip()
    except Exception as e:
        log.warning("Telegram: erro no /api/chat: %s", e)
    return "(sem resposta do cérebro no momento)"


def _send(url: str, chat_id: int, text: str):
    try:
        httpx.post(url + "sendMessage",
                   json={"chat_id": chat_id, "text": text[:4000]},
                   timeout=20)
    except Exception:
        pass


def start_telegram_bot():
    """Inicia o loop do bot em thread daemon. No-op se não houver token."""
    tok = _token()
    if not tok:
        log.info("Telegram: sem TELEGRAM_BOT_TOKEN — bot desativado.")
        return
    base = _public_base()
    owner_tok = _owner_token(base)
    if not owner_tok:
        log.warning("Telegram: não consegui obter token do dono — bot desativado.")
        return

    url = _POLL.format(tok)
    state = {"offset": 0}
    log.info("Telegram bot iniciado (base=%s).", base)

    def _loop():
        while True:
            try:
                r = httpx.get(url + "getUpdates",
                             params={"offset": state["offset"], "timeout": 30},
                             timeout=35)
                if r.status_code == 200:
                    for upd in r.json().get("result", []):
                        state["offset"] = upd["update_id"] + 1
                        msg = upd.get("message") or upd.get("edited_message")
                        if not msg:
                            continue
                        chat_id = msg["chat"]["id"]
                        text = (msg.get("text") or "").strip()
                        if not text:
                            continue
                        if text.startswith("/start"):
                            _send(url, chat_id,
                                  "Olá! Eu sou o JARVIS. Pergunte qualquer coisa, "
                                  "ou mande 'envie um email para voce@email.com assunto Oi dizendo Tudo bem'.")
                            continue
                        _send(url, chat_id, _answer(base, owner_tok, text))
            except Exception as e:
                log.warning("Telegram loop erro: %s", e)
                time.sleep(5)

    threading.Thread(target=_loop, daemon=True).start()
