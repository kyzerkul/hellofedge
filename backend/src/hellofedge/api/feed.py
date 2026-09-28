"""État du flux de prix (spec 0002, AC-11) : `GET /api/feed/status`.

Source active, heure de la dernière bougie, coupure en cours. Aucun jeton ni
identifiant de compte n'est renvoyé.
"""

from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine

from hellofedge.api.auth import SessionDep
from hellofedge.config import get_settings
from hellofedge.data import outages, store


class Outage(BaseModel):
    started_at: datetime
    cause: str


class FeedStatus(BaseModel):
    source: str
    last_ts_open: datetime | None
    outage: Outage | None


async def feed_status(engine: AsyncEngine, source: str) -> FeedStatus:
    last = await store.last_ts_open(engine, source)
    open_ = await outages.current(engine, source)
    return FeedStatus(
        source=source,
        last_ts_open=last,
        outage=None
        if open_ is None
        else Outage(started_at=open_.started_at, cause=open_.cause),
    )


router = APIRouter(prefix="/api/feed", tags=["flux"])


@router.get("/status")
async def status(request: Request, _session: SessionDep) -> FeedStatus:
    return await feed_status(request.app.state.engine, get_settings().price_source)
