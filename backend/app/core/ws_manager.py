"""Gerenciador global de conexões WebSocket ativas do NEXUS AI.

Mantém um registro thread-safe de todas as conexões WebSocket abertas por user_id.
Permite que serviços de background (scheduler de lembretes, auto-melhoria, etc.)
enviem mensagens aos usuários conectados sem precisar de polling.

Uso:
    from app.core.ws_manager import manager

    # No endpoint WebSocket:
    manager.connect(user.id, websocket)
    try:
        ...
    finally:
        manager.disconnect(user.id, websocket)

    # Em qualquer thread de background:
    manager.push_sync(user_id, {"type": "reminder", "title": "..."})
"""
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("nexus.ws_manager")


class ConnectionManager:
    def __init__(self):
        # user_id -> set de WebSockets ativos
        self._conns: Dict[int, Set[WebSocket]] = defaultdict(set)
        # Loop asyncio capturado na primeira conexão (para uso em threads)
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── Registro de conexões ─────────────────────────────────────────────────

    def connect(self, user_id: int, ws: WebSocket) -> None:
        self._conns[user_id].add(ws)
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            pass
        logger.debug("WS+: user=%d  total=%d conexões", user_id, len(self._conns[user_id]))

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        self._conns[user_id].discard(ws)
        if not self._conns[user_id]:
            self._conns.pop(user_id, None)
        logger.debug("WS-: user=%d", user_id)

    # ── Envio de mensagens ───────────────────────────────────────────────────

    async def push(self, user_id: int, payload: dict) -> int:
        """Envia payload JSON para todas as conexões ativas do usuário.
        Retorna o número de conexões que receberam a mensagem com sucesso."""
        dead: Set[WebSocket] = set()
        sent = 0
        for ws in list(self._conns.get(user_id, set())):
            try:
                await ws.send_json(payload)
                sent += 1
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._conns[user_id].discard(ws)
        return sent

    def push_sync(self, user_id: int, payload: dict) -> bool:
        """Versão síncrona de push — para chamada de threads de background.
        Retorna True se havia loop asyncio disponível (mensagem enfileirada)."""
        if not self._conns.get(user_id):
            return False
        if self._loop is None or self._loop.is_closed():
            return False
        try:
            asyncio.run_coroutine_threadsafe(self.push(user_id, payload), self._loop)
            return True
        except Exception as e:
            logger.warning("WS push_sync falhou: %s", e)
            return False

    def broadcast_sync(self, payload: dict) -> int:
        """Envia para TODOS os usuários conectados (broadcast). Retorna quantos foram atingidos."""
        count = 0
        for uid in list(self._conns):
            if self.push_sync(uid, payload):
                count += 1
        return count

    def active_users(self) -> list[int]:
        """Retorna lista de user_ids com conexões ativas."""
        return [uid for uid, conns in self._conns.items() if conns]


# Singleton global — importar sempre daqui
manager = ConnectionManager()
