"""Chargement d'une période de bougies M1 chez le fournisseur, semaine par semaine
(spec 0002, AC-3, AC-6, AC-10).

Idempotent et reprenable : une minute déjà en base est ignorée (jamais réécrite, une
différence va dans `candle_revision`). Sert à `hellofedge feed backfill` et au
rattrapage du `worker` après une coupure ou un redémarrage.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncEngine

from hellofedge.data.feed import PriceFeed
from hellofedge.data.store import store_candles

log = logging.getLogger("hellofedge.data.backfill")

WEEK = timedelta(days=7)


@dataclass
class BackfillResult:
    inserted: int = 0
    ignored: int = 0
    revisions: int = 0
    # Plus ancienne bougie renvoyée par le fournisseur sur la période demandée.
    oldest: datetime | None = None


async def backfill(
    engine: AsyncEngine,
    feed: PriceFeed,
    start: datetime,
    end: datetime,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> BackfillResult:
    """Charge `[start, end)` et stocke les bougies avec `backfilled = true`."""
    result = BackfillResult()
    cursor = start
    while cursor < end:
        stop = min(cursor + WEEK, end)
        candles = await feed.history(cursor, stop)
        if candles and result.oldest is None:
            result.oldest = candles[0].ts_open
        stored = await store_candles(
            engine, feed.name, candles, backfilled=True, now=clock()
        )
        result.inserted += len(stored.inserted)
        result.ignored += stored.ignored
        result.revisions += stored.revisions
        log.info(
            "tranche chargée",
            extra={
                "data": {
                    "source": feed.name,
                    "debut": cursor.isoformat(),
                    "fin": stop.isoformat(),
                    "inserees": len(stored.inserted),
                    "ignorees": stored.ignored,
                    "revisions": stored.revisions,
                }
            },
        )
        cursor = stop
    return result
