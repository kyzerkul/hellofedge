"""Flux en direct du `worker` (spec 0002, AC-4, AC-5, AC-6), en temps simulé contre
une vraie base. Les scénarios suivent les « Critical test scenarios » de la spec."""

import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest
import pytest_asyncio
from sqlalchemy import select, text
from test_measure import FakeClock
from test_migrations import alembic

from hellofedge.data.candle import M1, Candle, PriceKind
from hellofedge.data.feed import FeedAuthError, FeedUnavailable
from hellofedge.data.market import MarketCalendar, parse_holidays
from hellofedge.data.models import CandleM1, FeedOutage
from hellofedge.data.pump import FeedPump, backoff
from hellofedge.data.store import store_candles
from hellofedge.db import make_engine

SOURCE = "fausse_source"
# Mardi 29 septembre 2026, 10h00 UTC (6h00 à New York) : marché ouvert.
TUESDAY_10H = datetime(2026, 9, 29, 10, 0, tzinfo=UTC)


def price_at(ts: datetime) -> Candle:
    base = Decimal("150.000") + Decimal(ts.minute) / 1000
    return Candle(ts, base, base + Decimal("0.010"), base - Decimal("0.010"), base)


class ReplayFeed:
    """Un fournisseur rejoué : chaque minute est disponible `lag` après sa fin.

    Pendant `mute` (heures réelles du faux horloge), il échoue avec `error`, ou ne
    renvoie rien si `error` vaut None.
    """

    name = SOURCE
    price_kind = PriceKind.BID

    def __init__(self, clock, *, lag=timedelta(seconds=1), mute=None, error=None):
        self.clock = clock
        self.lag = lag
        self.mute = mute
        self.error = error
        self.asked: list[datetime] = []
        self.maintained = 0

    def muted(self) -> bool:
        return self.mute is not None and self.mute[0] <= self.clock() < self.mute[1]

    async def maintain(self):
        self.maintained += 1

    async def aclose(self):
        pass

    async def history(self, start, end):
        raise AssertionError("le direct passe par closed_since")

    async def closed_since(self, after):
        now = self.clock()
        self.asked.append(now)
        if self.muted():
            if self.error is not None:
                raise self.error
            return []
        out, ts = [], after + M1
        while ts + M1 + self.lag <= now:
            out.append(price_at(ts))
            ts += M1
        return out


@pytest_asyncio.fixture
async def engine(db_url):
    result = alembic("upgrade", "head", database_url=db_url)
    assert result.returncode == 0, result.stderr
    eng = make_engine(db_url)
    async with eng.begin() as conn:
        await conn.execute(text("TRUNCATE candle_m1, candle_revision, feed_outage"))
    yield eng
    await eng.dispose()


async def run_until(pump: FeedPump, clock: FakeClock, end: datetime) -> None:
    await pump.start()
    while clock.now < end:
        await pump.step()


def make_pump(engine, feed, clock, holidays="12-25,01-01") -> FeedPump:
    return FeedPump(
        engine,
        feed,
        MarketCalendar(parse_holidays(holidays)),
        clock=clock,
        sleep=clock.sleep,
    )


async def stored(engine):
    async with engine.connect() as conn:
        return list(
            await conn.execute(
                select(*CandleM1.__table__.columns).order_by(CandleM1.ts_open)
            )
        )


async def outages(engine):
    async with engine.connect() as conn:
        return list(
            await conn.execute(
                select(*FeedOutage.__table__.columns).order_by(FeedOutage.id)
            )
        )


async def seed_last(engine, ts: datetime) -> None:
    await store_candles(engine, SOURCE, [price_at(ts)], backfilled=False, now=ts + M1)


@pytest.mark.asyncio
async def test_normal_path_stores_each_minute_once_and_in_time(engine):
    # Chemin normal (AC-3, AC-4) : deux heures rejouées.
    start = TUESDAY_10H
    clock = FakeClock(start + timedelta(seconds=30))
    await seed_last(engine, start - M1)
    feed = ReplayFeed(clock)

    await run_until(make_pump(engine, feed, clock), clock, start + timedelta(hours=2))

    rows = await stored(engine)
    minutes = [r.ts_open for r in rows]
    assert minutes == [start - M1 + i * M1 for i in range(len(minutes))]
    assert minutes[-1] >= start + timedelta(hours=2) - 2 * M1
    live = [r for r in rows if r.ts_open >= start]
    assert not any(r.backfilled for r in live)
    delays = [(r.received_at - (r.ts_open + M1)).total_seconds() for r in live]
    assert max(delays) < 10
    assert await outages(engine) == []


@pytest.mark.asyncio
async def test_a_five_minute_silence_opens_then_closes_an_outage(engine):
    # Scénario « panne » (AC-5, AC-6) : le fournisseur se tait 5 minutes à 10h00.
    clock = FakeClock(TUESDAY_10H - timedelta(minutes=5) + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - timedelta(minutes=6))
    feed = ReplayFeed(
        clock,
        mute=(TUESDAY_10H, TUESDAY_10H + timedelta(minutes=5)),
        error=FeedUnavailable("injoignable", "reseau"),
    )

    await run_until(
        make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=10)
    )

    (outage,) = await outages(engine)
    assert outage.cause == "reseau"
    silence = outage.started_at - (TUESDAY_10H - timedelta(seconds=57))
    assert timedelta(minutes=2) <= silence < timedelta(minutes=2, seconds=10)
    assert outage.closed_reason == "retour_flux"
    assert outage.bars_backfilled == 5
    assert outage.ended_at < TUESDAY_10H + timedelta(minutes=6)
    rows = await stored(engine)
    minutes = [r.ts_open for r in rows]
    # Ni trou ni doublon.
    assert minutes == [minutes[0] + i * M1 for i in range(len(minutes))]
    backfilled = [r.ts_open for r in rows if r.backfilled]
    assert backfilled == [TUESDAY_10H - M1 + i * M1 for i in range(5)]


@pytest.mark.asyncio
async def test_an_empty_answer_is_a_data_outage(engine):
    clock = FakeClock(TUESDAY_10H - timedelta(minutes=2) + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - timedelta(minutes=3))
    feed = ReplayFeed(clock, mute=(TUESDAY_10H, TUESDAY_10H + timedelta(hours=1)))

    await run_until(
        make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=5)
    )

    (outage,) = await outages(engine)
    assert outage.cause == "donnees_absentes" and outage.ended_at is None


@pytest.mark.asyncio
async def test_an_auth_refusal_gives_an_auth_outage(engine):
    clock = FakeClock(TUESDAY_10H - timedelta(minutes=2) + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - timedelta(minutes=3))
    feed = ReplayFeed(
        clock,
        mute=(TUESDAY_10H, TUESDAY_10H + timedelta(hours=1)),
        error=FeedAuthError("jeton refusé"),
    )

    await run_until(
        make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=5)
    )

    (outage,) = await outages(engine)
    assert outage.cause == "auth"


@pytest.mark.asyncio
async def test_no_outage_on_a_silent_saturday(engine):
    # Scénario « pas de fausse panne » (AC-5) : samedi 3 octobre 2026.
    saturday = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    clock = FakeClock(saturday)
    await seed_last(engine, saturday - timedelta(hours=20))
    feed = ReplayFeed(clock, mute=(saturday, saturday + timedelta(days=1)))

    await run_until(
        make_pump(engine, feed, clock), clock, saturday + timedelta(hours=1)
    )

    assert await outages(engine) == []
    # Marché fermé : on n'interroge même pas le fournisseur.
    assert feed.asked == []


@pytest.mark.asyncio
async def test_no_outage_during_the_rollover(engine):
    # Mercredi 30 septembre 2026, 17h02 à New York (21h02 UTC) : silence de 8 minutes.
    rollover = datetime(2026, 9, 30, 21, 2, tzinfo=UTC)
    clock = FakeClock(rollover - timedelta(minutes=4) + timedelta(seconds=30))
    await seed_last(engine, rollover - timedelta(minutes=5))
    feed = ReplayFeed(clock, mute=(rollover, rollover + timedelta(minutes=8)))

    await run_until(
        make_pump(engine, feed, clock), clock, rollover + timedelta(minutes=12)
    )

    assert await outages(engine) == []


@pytest.mark.asyncio
async def test_no_outage_on_a_configured_holiday(engine):
    # Vendredi 25 décembre 2026 : jour férié configuré.
    christmas = datetime(2026, 12, 25, 15, 0, tzinfo=UTC)
    clock = FakeClock(christmas)
    await seed_last(engine, christmas - timedelta(hours=10))
    feed = ReplayFeed(clock, mute=(christmas, christmas + timedelta(days=1)))

    await run_until(
        make_pump(engine, feed, clock), clock, christmas + timedelta(hours=1)
    )

    assert await outages(engine) == []


@pytest.mark.asyncio
async def test_an_open_outage_is_closed_when_the_market_closes(engine):
    # Scénario « week-end » : coupure ouverte le vendredi 2 octobre 2026 vers 16h50
    # à New York (20h50 UTC), fermée à 17h00 (21h00 UTC) avec fermeture_marche.
    friday_close = datetime(2026, 10, 2, 21, 0, tzinfo=UTC)
    clock = FakeClock(friday_close - timedelta(minutes=15) + timedelta(seconds=30))
    await seed_last(engine, friday_close - timedelta(minutes=16))
    mute_from = friday_close - timedelta(minutes=12)
    feed = ReplayFeed(
        clock,
        mute=(mute_from, friday_close + timedelta(days=3)),
        error=FeedUnavailable("injoignable", "reseau"),
    )

    await run_until(
        make_pump(engine, feed, clock), clock, friday_close + timedelta(minutes=10)
    )

    (outage,) = await outages(engine)
    assert friday_close - timedelta(minutes=11) < outage.started_at
    assert outage.started_at < friday_close - timedelta(minutes=9)
    assert outage.closed_reason == "fermeture_marche"
    assert outage.ended_at == friday_close


@pytest.mark.asyncio
async def test_a_restart_catches_up_the_missing_minutes(engine):
    # Rattrapage au démarrage (AC-6) : 10 minutes manquent.
    clock = FakeClock(TUESDAY_10H + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - timedelta(minutes=11))
    feed = ReplayFeed(clock)

    await run_until(
        make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=3)
    )

    rows = await stored(engine)
    minutes = [r.ts_open for r in rows]
    assert minutes == [minutes[0] + i * M1 for i in range(len(minutes))]
    catch_up = [r.ts_open for r in rows if r.backfilled]
    assert catch_up == [TUESDAY_10H - timedelta(minutes=10) + i * M1 for i in range(9)]
    assert await outages(engine) == []


@pytest.mark.asyncio
async def test_each_new_candle_is_announced_by_notify(engine, db_url):
    clock = FakeClock(TUESDAY_10H + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - M1)
    feed = ReplayFeed(clock)
    with psycopg.connect(db_url, autocommit=True) as listener:
        listener.execute("LISTEN candle_m1")

        await run_until(
            make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=3)
        )

        payloads = [
            json.loads(n.payload) for n in listener.notifies(timeout=1, stop_after=3)
        ]

    assert payloads[0] == {"source": SOURCE, "ts_open": "2026-09-29T10:00:00Z"}
    assert [p["ts_open"] for p in payloads] == [
        "2026-09-29T10:00:00Z",
        "2026-09-29T10:01:00Z",
        "2026-09-29T10:02:00Z",
    ]


@pytest.mark.asyncio
async def test_the_first_ask_is_at_second_3_and_maintenance_runs(engine):
    clock = FakeClock(TUESDAY_10H + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - M1)
    feed = ReplayFeed(clock)

    await run_until(
        make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=3)
    )

    assert feed.asked[0] == TUESDAY_10H + M1 + timedelta(seconds=3)
    assert feed.maintained == 1


def test_backoff_doubles_up_to_60_seconds():
    assert [backoff(n) for n in range(1, 8)] == [2, 4, 8, 16, 32, 60, 60]


class TestMarketCalendar:
    cal = MarketCalendar(parse_holidays("12-25,01-01"))

    @pytest.mark.parametrize(
        ("ts", "is_open"),
        [
            (datetime(2026, 10, 2, 20, 59, tzinfo=UTC), True),  # vendredi 16h59 NY
            (datetime(2026, 10, 2, 21, 0, tzinfo=UTC), False),  # vendredi 17h00 NY
            (datetime(2026, 10, 3, 12, 0, tzinfo=UTC), False),  # samedi
            (datetime(2026, 10, 4, 20, 59, tzinfo=UTC), False),  # dimanche 16h59 NY
            (datetime(2026, 10, 4, 21, 0, tzinfo=UTC), True),  # dimanche 17h00 NY
            (
                datetime(2026, 1, 16, 22, 0, tzinfo=UTC),
                False,
            ),  # vendredi 17h00 NY (hiver)
            (datetime(2026, 1, 16, 21, 59, tzinfo=UTC), True),
            (datetime(2026, 12, 25, 15, 0, tzinfo=UTC), False),  # Noël
            (datetime(2027, 1, 1, 15, 0, tzinfo=UTC), False),  # 1er janvier
        ],
    )
    def test_open_hours_follow_new_york_time(self, ts, is_open):
        assert self.cal.is_open(ts) is is_open

    def test_rollover_window_is_16h58_to_17h10_new_york(self):
        assert not self.cal.in_rollover(datetime(2026, 9, 30, 20, 57, tzinfo=UTC))
        assert self.cal.in_rollover(datetime(2026, 9, 30, 20, 58, tzinfo=UTC))
        assert self.cal.in_rollover(datetime(2026, 9, 30, 21, 9, tzinfo=UTC))
        assert not self.cal.in_rollover(datetime(2026, 9, 30, 21, 10, tzinfo=UTC))

    def test_closed_at_is_the_start_of_the_closure(self):
        saturday = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)

        assert self.cal.closed_at(saturday) == datetime(2026, 10, 2, 21, 0, tzinfo=UTC)

    def test_holidays_must_be_real_dates(self):
        with pytest.raises(ValueError):
            parse_holidays("13-40")
        assert parse_holidays("") == frozenset()


@pytest.mark.asyncio
async def test_a_failed_poll_is_logged_with_its_minute_and_time(engine, caplog):
    # AC-4 : chaque interrogation, réussie ou non, dit la minute visée et l'heure.
    caplog.set_level(logging.INFO, logger="hellofedge.data.pump")
    clock = FakeClock(TUESDAY_10H + timedelta(seconds=30))
    await seed_last(engine, TUESDAY_10H - M1)
    feed = ReplayFeed(
        clock,
        mute=(TUESDAY_10H, TUESDAY_10H + timedelta(minutes=1, seconds=5)),
        error=FeedUnavailable("injoignable", "reseau"),
    )

    await run_until(
        make_pump(engine, feed, clock), clock, TUESDAY_10H + timedelta(minutes=2)
    )

    polls = [
        r.data
        for r in caplog.records
        if r.getMessage().startswith("interrogation du fournisseur")
    ]
    failed = [p for p in polls if "cause" in p]
    assert failed and len(failed) < len(polls)
    for p in polls:
        assert set(p) >= {"minute", "demande"}
    first = failed[0]
    assert first["minute"] == TUESDAY_10H.isoformat()
    assert (
        first["demande"] == (TUESDAY_10H + timedelta(minutes=1, seconds=3)).isoformat()
    )


class SlowFailingFeed(ReplayFeed):
    """Comme sur le VPS sans cTrader : chaque essai muet prend 5 secondes (délai
    de connexion) avant d'échouer."""

    async def closed_since(self, after):
        if self.muted():
            await self.clock.sleep(5)
        return await super().closed_since(after)


@pytest.mark.asyncio
async def test_growing_waits_never_delay_the_outage_past_two_minutes(engine):
    # AC-5 : l'attente croissante entre deux essais (2, 4, 8, 16, 32 s) ne fait
    # pas ouvrir la coupure en retard.
    clock = FakeClock(TUESDAY_10H - timedelta(seconds=10))
    await seed_last(engine, TUESDAY_10H - 2 * M1)
    feed = SlowFailingFeed(
        clock,
        mute=(TUESDAY_10H - timedelta(minutes=1), TUESDAY_10H + timedelta(hours=1)),
        error=FeedUnavailable("délai dépassé", "timeout"),
    )
    pump = make_pump(engine, feed, clock)

    await run_until(pump, clock, TUESDAY_10H + timedelta(minutes=4))

    (outage,) = await outages(engine)
    assert outage.cause == "timeout"
    silence = outage.started_at - (TUESDAY_10H - timedelta(seconds=10))
    # 2 minutes, plus au plus un essai de 5 secondes en cours.
    assert timedelta(minutes=2) <= silence <= timedelta(minutes=2, seconds=5)
