"""Bougies en base (spec 0002, AC-3, AC-10) : vraie base, vraie migration."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest
import pytest_asyncio
from fake_ctrader import FakeCTrader
from sqlalchemy import select, text
from test_ctrader_feed import Market
from test_feed_commands import settings
from test_measure import FakeFeed
from test_migrations import alembic

from hellofedge import cli
from hellofedge.data.backfill import backfill
from hellofedge.data.candle import M1, Candle
from hellofedge.data.models import CandleM1, CandleRevision
from hellofedge.data.store import first_ts_open, last_ts_open, store_candles
from hellofedge.db import make_engine

SOURCE = "ctrader_icmarkets"
T0 = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def candle(ts: datetime, close: str = "159.105") -> Candle:
    c = Decimal(close)
    return Candle(
        ts, Decimal("159.100"), max(c, Decimal("159.110")), Decimal("159.090"), c
    )


@pytest_asyncio.fixture
async def engine(db_url):
    result = alembic("upgrade", "head", database_url=db_url)
    assert result.returncode == 0, result.stderr
    eng = make_engine(db_url)
    async with eng.begin() as conn:
        await conn.execute(text("TRUNCATE candle_m1, candle_revision, feed_outage"))
    yield eng
    await eng.dispose()


async def rows(engine, model):
    async with engine.connect() as conn:
        return list(await conn.execute(select(*model.__table__.columns)))


@pytest.mark.asyncio
async def test_candles_are_stored_once_per_source_and_minute(engine):
    candles = [candle(T0 + i * M1) for i in range(3)]

    first = await store_candles(engine, SOURCE, candles, backfilled=False, now=NOW)
    second = await store_candles(engine, SOURCE, candles, backfilled=False, now=NOW)

    assert first.inserted == [c.ts_open for c in candles] and first.ignored == 0
    assert second.inserted == [] and second.ignored == 3 and second.revisions == 0
    assert len(await rows(engine, CandleM1)) == 3


@pytest.mark.asyncio
async def test_prices_come_back_as_exact_decimals_in_utc(engine):
    await store_candles(engine, SOURCE, [candle(T0)], backfilled=True, now=NOW)

    (row,) = await rows(engine, CandleM1)

    assert row.close == Decimal("159.105") and row.low == Decimal("159.090")
    assert row.ts_open == T0 and row.ts_open.utcoffset() == timedelta(0)
    assert row.backfilled is True and row.received_at == NOW


@pytest.mark.asyncio
async def test_another_source_keeps_its_own_candles(engine):
    # AC-8 : les bougies des autres sources restent en base.
    await store_candles(engine, SOURCE, [candle(T0)], backfilled=False, now=NOW)
    await store_candles(engine, "fundednext", [candle(T0)], backfilled=False, now=NOW)

    assert len(await rows(engine, CandleM1)) == 2
    assert await last_ts_open(engine, SOURCE) == T0
    assert await last_ts_open(engine, "inconnue") is None


@pytest.mark.asyncio
async def test_a_different_value_later_is_a_revision_not_a_rewrite(engine):
    # Scénario « révision » (AC-10).
    await store_candles(engine, SOURCE, [candle(T0)], backfilled=False, now=NOW)
    later = NOW + timedelta(hours=1)

    result = await store_candles(
        engine, SOURCE, [candle(T0, close="159.108")], backfilled=True, now=later
    )

    (row,) = await rows(engine, CandleM1)
    assert row.close == Decimal("159.105") and row.backfilled is False
    (rev,) = await rows(engine, CandleRevision)
    assert (rev.champ, rev.valeur_stockee, rev.valeur_recue) == (
        "close",
        Decimal("159.105"),
        Decimal("159.108"),
    )
    assert rev.detected_at == later
    assert result.revisions == 1


@pytest.mark.asyncio
async def test_the_same_revision_is_noted_only_once(engine):
    await store_candles(engine, SOURCE, [candle(T0)], backfilled=False, now=NOW)
    for _ in range(2):
        await store_candles(
            engine, SOURCE, [candle(T0, close="159.108")], backfilled=True, now=NOW
        )

    assert len(await rows(engine, CandleRevision)) == 1


@pytest.mark.asyncio
async def test_large_loads_are_split_under_the_parameter_limit(engine):
    candles = [candle(T0 + i * M1) for i in range(2500)]

    result = await store_candles(engine, SOURCE, candles, backfilled=True, now=NOW)

    assert len(result.inserted) == 2500
    assert await first_ts_open(engine, SOURCE) == T0


class TestDatabaseRules:
    def insert(self, db_url, ts, o="1.000", h="1.000", low="1.000", c="1.000"):
        with psycopg.connect(db_url) as conn:
            conn.execute(
                "INSERT INTO candle_m1 (source, ts_open, open, high, low, close, "
                "received_at) VALUES ('x', %s, %s, %s, %s, %s, now())",
                (ts, o, h, low, c),
            )

    def test_a_time_that_is_not_a_full_minute_is_refused(self, db_url, engine):
        with pytest.raises(psycopg.errors.CheckViolation):
            self.insert(db_url, T0 + timedelta(seconds=30))

    def test_an_incoherent_candle_is_refused(self, db_url, engine):
        with pytest.raises(psycopg.errors.CheckViolation):
            self.insert(db_url, T0, o="1.000", h="0.990", low="0.980", c="1.000")

    def test_only_one_open_outage_per_source(self, db_url, engine):
        with psycopg.connect(db_url) as conn:
            conn.execute(
                "INSERT INTO feed_outage (source, started_at, cause) "
                "VALUES ('x', now(), 'timeout')"
            )
            with pytest.raises(psycopg.errors.UniqueViolation):
                conn.execute(
                    "INSERT INTO feed_outage (source, started_at, cause) "
                    "VALUES ('x', now(), 'reseau')"
                )

    def test_an_unknown_outage_cause_is_refused(self, db_url, engine):
        with (
            psycopg.connect(db_url) as conn,
            pytest.raises(psycopg.errors.CheckViolation),
        ):
            conn.execute(
                "INSERT INTO feed_outage (source, started_at, cause) "
                "VALUES ('x', now(), 'inconnue')"
            )


@pytest.mark.asyncio
async def test_backfill_goes_week_by_week_and_notes_the_oldest_candle(engine):
    start = datetime(2026, 8, 3, tzinfo=UTC)
    feed = FakeFeed([candle(T0 + i * M1) for i in range(5)])
    feed.name = SOURCE

    result = await backfill(engine, feed, start, start + timedelta(days=30))

    assert len(feed.calls) == 5
    assert result.inserted == 5 and result.oldest == T0


@pytest.mark.asyncio
async def test_backfill_command_run_twice_inserts_nothing_the_second_time(
    db_url, engine, clean_token, on_fake
):
    # Scénario « relance » (AC-3).
    start, end = T0, T0 + timedelta(days=2)
    async with FakeCTrader() as fake:
        Market(fake).fill(T0, 300)
        on_fake(fake)

        first = await cli.feed_backfill(settings(db_url), NOW, start, end)
        second = await cli.feed_backfill(settings(db_url), NOW, start, end)

    assert first.inserted == 300 and first.oldest == T0
    assert second.inserted == 0 and second.ignored == 300
    assert all(r.backfilled for r in await rows(engine, CandleM1))
