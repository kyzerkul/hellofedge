"""Adaptateur `ctrader_icmarkets` : bougies M1 bid lues sur cTrader (spec 0002).

Il suit l'interface `PriceFeed`. À chaque connexion, il authentifie le compte puis
lit l'identifiant et les décimales du symbole (`CTRADER_SYMBOL`), jamais écrits en dur.

- `history` demande les bougies par tranches d'une semaine. Une tranche qui revient
  pleine (14 000 bougies, ou `hasMore`) a peut-être été tronquée par cTrader sans
  erreur : on la redécoupe en deux et on redemande chaque moitié.
- `closed_since` s'arrête au début de la minute en cours (exclue) : la bougie en
  formation n'est jamais renvoyée.
- Prix = (`low` + delta) / 100 000, arrondi aux décimales du symbole, en `Decimal`.
  Heure d'ouverture = `utcTimestampInMinutes` × 60 secondes, en UTC.

Les demandes de bougies passent par le limiteur partagé de la connexion (4 par seconde,
sous la limite de 5 de cTrader). La reconnexion avec attente croissante appartient à
l'appelant (le `worker`) : ici, une connexion perdue est rouverte au prochain appel.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from hellofedge.data.candle import M1, Candle, PriceKind, check_utc_minute
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.token import SOURCE
from hellofedge.data.ctrader.protocol import (
    MAX_BARS_PER_REQUEST,
    PERIOD_M1,
    PRICE_SCALE,
    Msg,
)
from hellofedge.data.feed import FeedAuthError, FeedUnavailable

log = logging.getLogger("hellofedge.data.ctrader")

# Une semaine de M1 fait au plus 10 080 bougies, sous la limite de 14 000.
CHUNK = timedelta(days=7)

# La base garde 3 décimales (NUMERIC(10,3)) : un symbole plus précis serait tronqué.
MAX_DIGITS = 3

Authorize = Callable[[CTraderClient, int], Awaitable[None]]


@dataclass(frozen=True)
class Symbol:
    symbol_id: int
    digits: int


def decode_bar(bar: dict[str, Any], digits: int) -> Candle:
    """Une bougie cTrader (`ProtoOATrendbar`) en `Candle` M1 bid.

    Les deltas à zéro peuvent être absents du message : ils valent alors 0.
    """
    low = int(bar["low"])
    step = Decimal(1).scaleb(-digits)

    def price(delta_field: str | None) -> Decimal:
        raw = low + (int(bar.get(delta_field, 0)) if delta_field else 0)
        return (Decimal(raw) / PRICE_SCALE).quantize(step, rounding=ROUND_HALF_UP)

    volume = bar.get("volume")
    return Candle(
        ts_open=datetime.fromtimestamp(int(bar["utcTimestampInMinutes"]) * 60, UTC),
        open=price("deltaOpen"),
        high=price("deltaHigh"),
        low=price(None),
        close=price("deltaClose"),
        tick_volume=None if volume is None else int(volume),
    )


def _ms(ts: datetime) -> int:
    return int(ts.timestamp()) * 1000


def _floor_minute(ts: datetime) -> datetime:
    return ts.astimezone(UTC).replace(second=0, microsecond=0)


class CTraderFeed:
    """Source `ctrader_icmarkets`, en lecture seule."""

    name = SOURCE
    price_kind = PriceKind.BID

    def __init__(
        self,
        client: CTraderClient,
        account_id: int,
        symbol_name: str,
        authorize: Authorize,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        chunk: timedelta = CHUNK,
        max_bars: int = MAX_BARS_PER_REQUEST,
    ) -> None:
        self.client = client
        self.account_id = account_id
        self.symbol_name = symbol_name
        self._authorize = authorize
        self._clock = clock
        self._chunk = chunk
        self._max_bars = max_bars
        self._symbol: Symbol | None = None
        # Direct et rattrapage partagent la connexion : une seule ouverture à la fois.
        self._ready_lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self.client.close()

    async def ensure_ready(self) -> Symbol:
        """Connexion ouverte, compte authentifié, symbole connu."""
        async with self._ready_lock:
            if not self.client.connected:
                self._symbol = None
                await self.client.connect()
            if self.client.authorized_account != self.account_id:
                await self._authorize(self.client, self.account_id)
            if self._symbol is None:
                self._symbol = await self._load_symbol()
            return self._symbol

    async def _load_symbol(self) -> Symbol:
        listing = await self.client.request(
            Msg.SYMBOLS_LIST_REQ, {"ctidTraderAccountId": self.account_id}
        )
        symbol_id = next(
            (
                int(s["symbolId"])
                for s in listing.get("symbol") or []
                if s.get("symbolName") == self.symbol_name
            ),
            None,
        )
        if symbol_id is None:
            raise FeedUnavailable(
                f"cTrader : symbole {self.symbol_name} absent de ce compte",
                "erreur_api",
            )
        detail = await self.client.request(
            Msg.SYMBOL_BY_ID_REQ,
            {"ctidTraderAccountId": self.account_id, "symbolId": [symbol_id]},
        )
        found = [
            s for s in detail.get("symbol") or [] if int(s["symbolId"]) == symbol_id
        ]
        if not found or "digits" not in found[0]:
            raise FeedUnavailable(
                f"cTrader : décimales de {self.symbol_name} introuvables", "erreur_api"
            )
        digits = int(found[0]["digits"])
        if not 0 <= digits <= MAX_DIGITS:
            raise FeedUnavailable(
                f"cTrader : {self.symbol_name} a {digits} décimales, la base en garde "
                f"{MAX_DIGITS} au plus",
                "erreur_api",
            )
        log.info(
            "symbole cTrader lu",
            extra={
                "data": {
                    "symbole": self.symbol_name,
                    "id": symbol_id,
                    "decimales": digits,
                }
            },
        )
        return Symbol(symbol_id, digits)

    async def _bars(self, start: datetime, end: datetime) -> dict[str, Any]:
        """Une demande de bougies M1. Sur un refus d'authentification, le compte est
        authentifié de nouveau (jeton relu en base) et la demande refaite une fois."""
        for attempt in (1, 2):
            symbol = await self.ensure_ready()
            try:
                return await self.client.trendbars(
                    {
                        "ctidTraderAccountId": self.account_id,
                        "symbolId": symbol.symbol_id,
                        "period": PERIOD_M1,
                        "fromTimestamp": _ms(start),
                        "toTimestamp": _ms(end),
                    }
                )
            except FeedAuthError:
                if attempt == 2:
                    raise
                self.client.authorized_account = None
        raise AssertionError("inatteignable")

    async def _range(self, start: datetime, end: datetime) -> list[Candle]:
        payload = await self._bars(start, end)
        bars = payload.get("trendbar") or []
        truncated = len(bars) >= self._max_bars or bool(payload.get("hasMore"))
        if truncated and end - start > M1:
            mid = start + (end - start) // 2
            mid = mid.replace(second=0, microsecond=0)
            log.info(
                "tranche cTrader pleine, redécoupée",
                extra={"data": {"debut": start.isoformat(), "fin": end.isoformat()}},
            )
            return await self._range(start, mid) + await self._range(mid, end)
        assert self._symbol is not None
        digits = self._symbol.digits
        return [
            c for c in (decode_bar(b, digits) for b in bars) if start <= c.ts_open < end
        ]

    async def history(self, start: datetime, end: datetime) -> list[Candle]:
        check_utc_minute(start)
        check_utc_minute(end)
        found: dict[datetime, Candle] = {}
        cursor = start
        while cursor < end:
            stop = min(cursor + self._chunk, end)
            for c in await self._range(cursor, stop):
                found.setdefault(c.ts_open, c)
            cursor = stop
        return [found[ts] for ts in sorted(found)]

    async def closed_since(self, after: datetime) -> list[Candle]:
        check_utc_minute(after)
        # Fin exclue : le début de la minute en cours, dont la bougie se forme encore.
        current = _floor_minute(self._clock())
        start = after + M1
        if start >= current:
            return []
        return await self.history(start, current)
