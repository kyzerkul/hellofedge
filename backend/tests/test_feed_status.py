"""État du flux (spec 0002, AC-11) : `GET /api/feed/status`."""

from datetime import timedelta

import pytest
from test_api import DOWN_URL, make_client  # noqa: F401
from test_store import NOW, SOURCE, T0, candle, engine  # noqa: F401

from hellofedge.api.feed import FeedStatus, Outage, feed_status
from hellofedge.data import outages
from hellofedge.data.store import store_candles


def test_status_requires_a_session(make_client):  # noqa: F811
    response = make_client(DOWN_URL).get("/api/feed/status")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_status_with_no_candle_yet(engine):  # noqa: F811
    assert await feed_status(engine, SOURCE) == FeedStatus(
        source=SOURCE, last_ts_open=None, outage=None
    )


@pytest.mark.asyncio
async def test_status_shows_last_candle_and_open_outage(engine):  # noqa: F811
    await store_candles(
        engine,
        SOURCE,
        [candle(T0), candle(T0 + timedelta(minutes=1))],
        backfilled=False,
        now=NOW,
    )
    await outages.open_outage(engine, SOURCE, NOW, "reseau")

    status = await feed_status(engine, SOURCE)

    assert status == FeedStatus(
        source=SOURCE,
        last_ts_open=T0 + timedelta(minutes=1),
        outage=Outage(started_at=NOW, cause="reseau"),
    )


@pytest.mark.asyncio
async def test_status_ignores_other_sources(engine):  # noqa: F811
    await store_candles(engine, "autre", [candle(T0)], backfilled=False, now=NOW)
    await outages.open_outage(engine, "autre", NOW, "auth")

    status = await feed_status(engine, SOURCE)

    assert status.last_ts_open is None and status.outage is None


def test_status_payload_carries_no_secret_field():
    assert set(FeedStatus.model_fields) == {"source", "last_ts_open", "outage"}
    assert set(Outage.model_fields) == {"started_at", "cause"}
