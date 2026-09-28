"""Faux serveur cTrader (JSON sur WebSocket), local, pour tester sans réseau.

Par défaut il accepte tout et répond à chaque requête par sa réponse attendue, avec
un contenu vide. Un test peut changer la réponse d'un type de message avec `on`.
"""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from websockets.asyncio.server import Server, ServerConnection, serve

from hellofedge.data.ctrader.protocol import RESPONSE_OF, Msg

# Une réponse : (payloadType, payload), ou None pour ne rien répondre.
Reply = tuple[int, dict[str, Any]] | None
Handler = Callable[[dict[str, Any]], Reply]


def error(code: str) -> Reply:
    return (Msg.OA_ERROR_RES, {"errorCode": code})


class FakeCTrader:
    def __init__(self) -> None:
        self.received: list[dict[str, Any]] = []
        self.handlers: dict[int, Handler] = {}
        self.connections: list[ServerConnection] = []
        self._server: Server | None = None

    def on(self, payload_type: int, handler: Handler) -> None:
        self.handlers[int(payload_type)] = handler

    def of_type(self, payload_type: int) -> list[dict[str, Any]]:
        return [f for f in self.received if f.get("payloadType") == payload_type]

    @property
    def url(self) -> str:
        assert self._server is not None
        port = next(iter(self._server.sockets)).getsockname()[1]
        return f"ws://127.0.0.1:{port}"

    async def __aenter__(self) -> "FakeCTrader":
        self._server = await serve(self._handle, "127.0.0.1", 0)
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self._server is not None
        self._server.close()
        await self._server.wait_closed()

    async def drop_all(self) -> None:
        """Coupe toutes les connexions, comme une panne réseau."""
        for conn in self.connections:
            await conn.close()

    async def _handle(self, conn: ServerConnection) -> None:
        self.connections.append(conn)
        async for raw in conn:
            frame = json.loads(raw)
            self.received.append(frame)
            kind = frame.get("payloadType")
            if kind == Msg.HEARTBEAT_EVENT:
                continue
            handler = self.handlers.get(kind)
            if handler is not None:
                reply = handler(frame.get("payload") or {})
            else:
                reply = (RESPONSE_OF[kind], {}) if kind in RESPONSE_OF else None
            if reply is None:
                continue
            out = {"payloadType": int(reply[0]), "payload": reply[1]}
            if "clientMsgId" in frame:
                out["clientMsgId"] = frame["clientMsgId"]
            await conn.send(json.dumps(out))
            await asyncio.sleep(0)
