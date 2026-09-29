"""Client cTrader : JSON sur WebSocket, en lecture seule.

Une connexion, authentifiée au niveau de l'application à l'ouverture. Le client
n'envoie que les messages de la liste blanche (`protocol.SENDABLE`), envoie un
maintien de connexion toutes les 10 secondes et partage un seul limiteur entre toutes
les demandes de bougies faites sur la connexion.

Il ne journalise jamais le contenu d'un message : seulement son type. Les jetons et
les identifiants de l'application n'apparaissent donc jamais dans les journaux.
"""

import asyncio
import contextlib
import itertools
import json
import logging
import time
from typing import Any

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, WebSocketException

from hellofedge.data.ctrader.protocol import (
    AUTH_ERROR_CODES,
    RATE_LIMIT_ERROR_CODES,
    RESPONSE_OF,
    SENDABLE,
    Msg,
)
from hellofedge.data.feed import (
    FeedAuthError,
    FeedError,
    FeedRateLimited,
    FeedUnavailable,
)

log = logging.getLogger("hellofedge.data.ctrader")

# Une réponse de 14 000 bougies dépasse la taille par défaut d'un message (1 Mo).
MAX_MESSAGE_BYTES = 16 * 1024 * 1024


class MessageNotAllowed(ValueError):
    """Message hors de la liste blanche : le client refuse de l'envoyer (AC-14)."""


def msg_name(payload_type: int) -> str:
    try:
        return Msg(payload_type).name
    except ValueError:
        return str(payload_type)


class RateLimiter:
    """Au plus `per_second` passages par seconde, régulièrement espacés.

    Un seul limiteur par connexion, partagé par toutes les tâches qui l'utilisent.
    """

    def __init__(self, per_second: float) -> None:
        self._interval = 1.0 / per_second
        self._next_at = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if self._next_at > now:
                await asyncio.sleep(self._next_at - now)
                now = time.monotonic()
            self._next_at = max(now, self._next_at) + self._interval


class CTraderClient:
    def __init__(
        self,
        url: str,
        client_id: str,
        client_secret: str,
        *,
        heartbeat_seconds: float = 10.0,
        request_timeout: float = 20.0,
        connect_timeout: float = 5.0,
        bars_per_second: float = 4.0,
    ) -> None:
        self.url = url
        self._client_id = client_id
        self._client_secret = client_secret
        self._heartbeat_seconds = heartbeat_seconds
        self._request_timeout = request_timeout
        # Ouvrir la connexion est rapide quand cTrader répond : un délai court fait
        # repartir vite le prochain essai quand il ne répond pas. Une grosse
        # requête de bougies, elle, garde `request_timeout`.
        self._connect_timeout = connect_timeout
        self.bars_limiter = RateLimiter(bars_per_second)
        self._ws: ClientConnection | None = None
        self._tasks: list[asyncio.Task[None]] = []
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._ids = itertools.count(1)
        self._connect_lock = asyncio.Lock()
        # Compte authentifié sur cette connexion. Remis à None à chaque nouvelle
        # connexion, ou quand cTrader signale que le compte ou le jeton ne vaut plus.
        self.authorized_account: int | None = None
        # Augmente à chaque connexion ouverte : ce qui a été lu sur une connexion
        # (le symbole) est relu sur la suivante.
        self.generation = 0

    @property
    def connected(self) -> bool:
        return self._ws is not None

    async def connect(self) -> None:
        """Ouvre la connexion (ou la rouvre) puis authentifie l'application."""
        async with self._connect_lock:
            await self._close()
            try:
                self._ws = await connect(
                    self.url,
                    open_timeout=self._connect_timeout,
                    max_size=MAX_MESSAGE_BYTES,
                    proxy=None,
                    # Le maintien est celui de cTrader (message 51), pas le ping WebSocket.
                    ping_interval=None,
                )
            except TimeoutError as exc:
                raise FeedUnavailable(
                    "cTrader : délai de connexion dépassé", "timeout"
                ) from exc
            except (OSError, WebSocketException) as exc:
                raise FeedUnavailable(
                    f"cTrader injoignable : {type(exc).__name__}", "reseau"
                ) from exc
            self.generation += 1
            self._tasks = [
                asyncio.create_task(self._read(self._ws)),
                asyncio.create_task(self._heartbeat(self._ws)),
            ]
            log.info("connexion cTrader ouverte", extra={"data": {"url": self.url}})
        try:
            await self.request(
                Msg.APPLICATION_AUTH_REQ,
                {"clientId": self._client_id, "clientSecret": self._client_secret},
            )
        except BaseException:
            await self.close()
            raise

    async def close(self) -> None:
        async with self._connect_lock:
            await self._close()

    async def _close(self) -> None:
        ws, self._ws = self._ws, None
        self.authorized_account = None
        tasks, self._tasks = self._tasks, []
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        if ws is not None:
            with contextlib.suppress(Exception):
                await ws.close()
        self._fail_pending(FeedUnavailable("connexion cTrader fermée", "reseau"))

    def _fail_pending(self, exc: Exception) -> None:
        pending, self._pending = self._pending, {}
        for fut in pending.values():
            if not fut.done():
                fut.set_exception(exc)

    async def _send(
        self, payload_type: int, payload: dict[str, Any], msg_id: str | None
    ) -> None:
        if payload_type not in SENDABLE:
            raise MessageNotAllowed(
                f"message {msg_name(payload_type)} hors de la liste blanche"
            )
        ws = self._ws
        if ws is None:
            raise FeedUnavailable("pas de connexion cTrader", "reseau")
        frame: dict[str, Any] = {"payloadType": int(payload_type), "payload": payload}
        if msg_id is not None:
            frame["clientMsgId"] = msg_id
        try:
            await ws.send(json.dumps(frame))
        except ConnectionClosed as exc:
            raise FeedUnavailable("connexion cTrader coupée", "reseau") from exc

    async def request(
        self, payload_type: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Envoie une requête de la liste blanche et renvoie le contenu de sa réponse."""
        if payload_type not in SENDABLE or payload_type not in RESPONSE_OF:
            raise MessageNotAllowed(
                f"message {msg_name(payload_type)} hors de la liste blanche"
            )
        msg_id = f"hf-{next(self._ids)}"
        fut: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[msg_id] = fut
        try:
            await self._send(payload_type, payload, msg_id)
            log.debug(
                "requête cTrader", extra={"data": {"type": msg_name(payload_type)}}
            )
            try:
                frame = await asyncio.wait_for(fut, self._request_timeout)
            except TimeoutError as exc:
                raise FeedUnavailable(
                    f"cTrader : pas de réponse à {msg_name(payload_type)}", "timeout"
                ) from exc
        finally:
            self._pending.pop(msg_id, None)
        return self._check_response(payload_type, frame)

    async def trendbars(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Demande de bougies, soumise au limiteur partagé de la connexion."""
        await self.bars_limiter.wait()
        return await self.request(Msg.GET_TRENDBARS_REQ, payload)

    @staticmethod
    def _check_response(sent: int, frame: dict[str, Any]) -> dict[str, Any]:
        received = frame.get("payloadType")
        payload = frame.get("payload") or {}
        if received in (Msg.ERROR_RES, Msg.OA_ERROR_RES):
            code = str(payload.get("errorCode", ""))
            text = f"cTrader refuse {msg_name(sent)} : {code}"
            exc: FeedError
            if code in AUTH_ERROR_CODES:
                exc = FeedAuthError(text)
            elif code in RATE_LIMIT_ERROR_CODES:
                exc = FeedRateLimited(text)
            else:
                exc = FeedUnavailable(text, "erreur_api")
            exc.error_code = code
            raise exc
        if received != RESPONSE_OF[sent]:
            raise FeedUnavailable(
                f"cTrader : réponse {msg_name(received or 0)} inattendue pour "
                f"{msg_name(sent)}",
                "erreur_api",
            )
        return payload

    async def _read(self, ws: ClientConnection) -> None:
        try:
            async for raw in ws:
                try:
                    frame = json.loads(raw)
                except ValueError:
                    log.warning("message cTrader illisible ignoré")
                    continue
                if not isinstance(frame, dict):
                    continue
                fut = self._pending.get(str(frame.get("clientMsgId")))
                if fut is not None and not fut.done():
                    fut.set_result(frame)
                    continue
                self._on_event(frame)
        except ConnectionClosed:
            pass
        finally:
            if self._ws is ws:
                log.warning("connexion cTrader perdue")
                self._ws = None
                self.authorized_account = None
            self._fail_pending(FeedUnavailable("connexion cTrader coupée", "reseau"))

    def _on_event(self, frame: dict[str, Any]) -> None:
        kind = frame.get("payloadType")
        if kind == Msg.HEARTBEAT_EVENT:
            return
        if kind in (Msg.ACCOUNTS_TOKEN_INVALIDATED_EVENT, Msg.ACCOUNT_DISCONNECT_EVENT):
            # Le compte doit être authentifié de nouveau avant la prochaine demande.
            self.authorized_account = None
        elif kind == Msg.CLIENT_DISCONNECT_EVENT and self._ws is not None:
            # cTrader va fermer : on considère la connexion perdue tout de suite.
            asyncio.get_running_loop().create_task(self._ws.close())
        log.info("événement cTrader", extra={"data": {"type": msg_name(kind or 0)}})

    async def _heartbeat(self, ws: ClientConnection) -> None:
        while True:
            await asyncio.sleep(self._heartbeat_seconds)
            try:
                await ws.send(
                    json.dumps({"payloadType": int(Msg.HEARTBEAT_EVENT), "payload": {}})
                )
            except ConnectionClosed:
                return
