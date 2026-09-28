"""Coupures de la source (`feed_outage`, spec 0002, AC-5, AC-6).

Au plus une coupure ouverte par source (index unique partiel en base). Le message
Telegram de panne appartient à la fonction « Surveillance de panne », qui lit
cette table.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from hellofedge.data.models import FeedOutage


@dataclass(frozen=True)
class OpenOutage:
    id: int
    started_at: datetime
    cause: str


async def current(engine: AsyncEngine, source: str) -> OpenOutage | None:
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(FeedOutage.id, FeedOutage.started_at, FeedOutage.cause).where(
                    FeedOutage.source == source, FeedOutage.ended_at.is_(None)
                )
            )
        ).first()
    return None if row is None else OpenOutage(row.id, row.started_at, row.cause)


async def open_outage(
    engine: AsyncEngine, source: str, at: datetime, cause: str
) -> OpenOutage:
    """Ouvre une coupure, ou renvoie celle déjà ouverte pour cette source."""
    stmt = (
        insert(FeedOutage)
        .values(source=source, started_at=at, cause=cause)
        .on_conflict_do_nothing(
            index_elements=[FeedOutage.source],
            index_where=FeedOutage.ended_at.is_(None),
        )
    )
    async with engine.begin() as conn:
        await conn.execute(stmt)
    found = await current(engine, source)
    assert found is not None
    return found


async def close_outage(
    engine: AsyncEngine,
    outage_id: int,
    at: datetime,
    reason: str,
    bars_backfilled: int = 0,
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            update(FeedOutage)
            .where(FeedOutage.id == outage_id, FeedOutage.ended_at.is_(None))
            .values(
                ended_at=at,
                closed_reason=reason,
                bars_backfilled=FeedOutage.bars_backfilled + bars_backfilled,
            )
        )
