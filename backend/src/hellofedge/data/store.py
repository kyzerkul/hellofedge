"""Écriture des bougies M1 en base (spec 0002, AC-3, AC-6, AC-10).

- Une seule bougie par `source` et par minute : l'insertion ignore une minute déjà
  stockée, relancer un chargement ne crée donc aucun doublon.
- Une bougie stockée n'est **jamais réécrite**. Si le fournisseur renvoie plus tard une
  autre valeur pour la même minute, la différence va dans `candle_revision` (une seule
  fois par valeur reçue), et la bougie stockée reste celle que le moteur a vue.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from hellofedge.data.candle import Candle
from hellofedge.data.models import REVISED_FIELDS, CandleM1, CandleRevision

# Lignes par requête : sous la limite de 65 535 paramètres de PostgreSQL.
BATCH = 1000


@dataclass(frozen=True)
class StoreResult:
    inserted: list[datetime]
    ignored: int
    revisions: int


async def store_candles(
    engine: AsyncEngine,
    source: str,
    candles: Sequence[Candle],
    *,
    backfilled: bool,
    now: datetime,
) -> StoreResult:
    inserted: list[datetime] = []
    ignored = revisions = 0
    for i in range(0, len(candles), BATCH):
        batch = candles[i : i + BATCH]
        async with engine.begin() as conn:
            new = await _insert(conn, source, batch, backfilled, now)
            already = [c for c in batch if c.ts_open not in new]
            revisions += await _record_revisions(conn, source, already, now)
        inserted += sorted(new)
        ignored += len(already)
    return StoreResult(inserted, ignored, revisions)


async def _insert(
    conn: AsyncConnection,
    source: str,
    batch: Sequence[Candle],
    backfilled: bool,
    now: datetime,
) -> set[datetime]:
    if not batch:
        return set()
    rows = [
        {
            "source": source,
            "ts_open": c.ts_open,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "ask_close": c.ask_close,
            "tick_volume": c.tick_volume,
            "backfilled": backfilled,
            "received_at": now,
        }
        for c in batch
    ]
    stmt = (
        insert(CandleM1)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[CandleM1.source, CandleM1.ts_open])
        .returning(CandleM1.ts_open)
    )
    return set((await conn.execute(stmt)).scalars())


async def _record_revisions(
    conn: AsyncConnection, source: str, received: Sequence[Candle], now: datetime
) -> int:
    """Note chaque champ qui diffère de la bougie stockée, sans jamais la modifier."""
    if not received:
        return 0
    keys = [c.ts_open for c in received]
    stored = {
        row.ts_open: row
        for row in await conn.execute(
            select(*CandleM1.__table__.columns).where(
                CandleM1.source == source, CandleM1.ts_open.in_(keys)
            )
        )
    }
    known = {
        (row.ts_open, row.champ, row.valeur_recue)
        for row in await conn.execute(
            select(
                CandleRevision.ts_open,
                CandleRevision.champ,
                CandleRevision.valeur_recue,
            ).where(
                CandleRevision.source == source,
                CandleRevision.ts_open.in_(keys),
            )
        )
    }
    rows = []
    for c in received:
        row = stored.get(c.ts_open)
        if row is None:
            continue
        for champ in REVISED_FIELDS:
            kept, got = getattr(row, champ), getattr(c, champ)
            if kept != got and (c.ts_open, champ, got) not in known:
                rows.append(
                    {
                        "source": source,
                        "ts_open": c.ts_open,
                        "champ": champ,
                        "valeur_stockee": kept,
                        "valeur_recue": got,
                        "detected_at": now,
                    }
                )
    if rows:
        await conn.execute(insert(CandleRevision).values(rows))
    return len(rows)


async def last_ts_open(engine: AsyncEngine, source: str) -> datetime | None:
    """Heure d'ouverture de la dernière bougie stockée pour `source`."""
    async with engine.connect() as conn:
        return (
            await conn.execute(
                select(func.max(CandleM1.ts_open)).where(CandleM1.source == source)
            )
        ).scalar_one()


async def first_ts_open(engine: AsyncEngine, source: str) -> datetime | None:
    async with engine.connect() as conn:
        return (
            await conn.execute(
                select(func.min(CandleM1.ts_open)).where(CandleM1.source == source)
            )
        ).scalar_one()
