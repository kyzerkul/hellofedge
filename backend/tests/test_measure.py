"""Mesure de la source contre OANDA (spec 0002, AC-2, AC-7, AC-12) et lecture du direct."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from hellofedge.data import measure
from hellofedge.data.candle import M1, Candle, PriceKind
from hellofedge.data.feed import FeedUnavailable
from hellofedge.data.live import wait_for_minute
from hellofedge.data.reference import PointType, ReferencePoint

T0 = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)


def candle(ts: datetime, o: str, h: str, low: str, c: str) -> Candle:
    return Candle(ts, Decimal(o), Decimal(h), Decimal(low), Decimal(c))


def point(
    ts: datetime,
    prix: str,
    champ: str = "open",
    kind: PointType = PointType.EXACT,
    ut: int = 1,
) -> ReferencePoint:
    return ReferencePoint("lot-1/ex1.png", ut, kind, ts, Decimal(prix), champ, "")


class FakeFeed:
    """Source en mémoire. `unavailable` fait échouer chaque appel."""

    name = "fausse_source"
    price_kind = PriceKind.BID

    def __init__(self, candles=(), *, now=None, unavailable=False) -> None:
        self.candles = {c.ts_open: c for c in candles}
        self.now = now
        self.unavailable = unavailable
        self.calls: list[tuple[datetime, datetime]] = []

    async def history(self, start, end):
        self.calls.append((start, end))
        if self.unavailable:
            raise FeedUnavailable("injoignable", "reseau")
        return [c for ts, c in sorted(self.candles.items()) if start <= ts < end]

    async def closed_since(self, after):
        current = self.now().replace(second=0, microsecond=0)
        return await self.history(after + M1, current)


class TestPointError:
    def test_exact_point_is_the_absolute_gap(self):
        c = candle(T0, "159.174", "159.190", "159.170", "159.180")

        assert measure.point_error(point(T0, "159.176"), c) == Decimal("0.002")
        assert measure.point_error(point(T0, "159.171"), c) == Decimal("0.003")

    def test_high_bound_is_respected_when_the_source_goes_at_least_as_high(self):
        c = candle(T0, "159.174", "159.190", "159.170", "159.180")
        bound = point(T0, "159.186", "high", PointType.BORNE)

        assert measure.point_error(bound, c) == 0

    def test_high_bound_counts_the_overshoot(self):
        c = candle(T0, "159.174", "159.190", "159.170", "159.180")
        bound = point(T0, "159.195", "high", PointType.BORNE)

        assert measure.point_error(bound, c) == Decimal("0.005")

    def test_low_bound_counts_the_overshoot(self):
        c = candle(T0, "159.174", "159.190", "159.170", "159.180")

        assert measure.point_error(point(T0, "159.172", "low", PointType.BORNE), c) == 0
        assert measure.point_error(
            point(T0, "159.168", "low", PointType.BORNE), c
        ) == Decimal("0.002")


class TestScore:
    def test_m3_points_use_candles_rebuilt_from_m1(self):
        # AC-7 : M3 calé sur :00, :03, :06, reconstruit depuis le M1.
        m1 = [
            candle(T0, "159.100", "159.110", "159.090", "159.105"),
            candle(T0 + M1, "159.105", "159.150", "159.100", "159.140"),
            candle(T0 + 2 * M1, "159.140", "159.145", "159.080", "159.120"),
        ]
        points = [
            point(T0, "159.100", "open", ut=3),
            point(T0, "159.150", "high", ut=3),
            point(T0, "159.080", "low", ut=3),
        ]

        results = measure.score(points, m1)

        assert [r.error for r in results] == [0, 0, 0]
        assert all(r.ok for r in results)

    def test_a_missing_candle_is_reported_and_counts_as_missed(self):
        results = measure.score([point(T0, "159.100")], [])

        assert results[0].source_value is None and not results[0].ok
        summary = measure.summarize(results)
        assert summary.missing == 1 and summary.share_ok == 0

    def test_a_one_minute_shift_is_revealed_by_the_neighbour(self):
        # AC-12 : la bougie d'avant colle au point, la bonne non.
        m1 = [
            candle(T0, "159.200", "159.210", "159.190", "159.205"),
            candle(T0 + M1, "159.300", "159.310", "159.290", "159.305"),
        ]

        result = measure.score([point(T0 + M1, "159.200")], m1)[0]

        assert not result.ok
        assert result.shift_hint == -1

    def test_no_shift_hint_when_the_point_matches(self):
        m1 = [candle(T0, "159.200", "159.210", "159.190", "159.205")]

        assert measure.score([point(T0, "159.200")], m1)[0].shift_hint is None


class TestSummary:
    def test_share_mean_and_max(self):
        c = candle(T0, "159.100", "159.110", "159.090", "159.105")
        results = measure.score(
            [
                point(T0, "159.100"),
                point(T0, "159.102"),
                point(T0, "159.110"),
                point(T0, "159.090"),
            ],
            [c],
        )

        s = measure.summarize(results)

        assert s.count == 4
        assert s.share_ok == 0.5
        assert s.mean_abs == Decimal("0.0055")
        assert s.max_abs == Decimal("0.010")
        assert not s.close_enough

    def test_ninety_percent_is_close_enough(self):
        c = candle(T0, "159.100", "159.110", "159.090", "159.105")
        points = [point(T0, "159.100")] * 9 + [point(T0, "159.200")]

        assert measure.summarize(measure.score(points, [c])).close_enough


class TestFetch:
    @pytest.mark.asyncio
    async def test_asks_one_window_per_day_with_a_margin(self):
        day2 = T0 + timedelta(days=1)
        feed = FakeFeed()
        points = [
            point(T0, "1.000"),
            point(T0 + 30 * M1, "1.000"),
            point(day2, "1.000"),
        ]

        await measure.fetch_for(feed, points)

        assert feed.calls == [
            (T0 - measure.MARGIN, T0 + 31 * M1 + measure.MARGIN),
            (day2 - measure.MARGIN, day2 + M1 + measure.MARGIN),
        ]

    @pytest.mark.asyncio
    async def test_oldest_candle_is_the_first_week_with_bars(self):
        now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
        oldest = datetime(2025, 3, 3, 0, 5, tzinfo=UTC)
        feed = FakeFeed(
            [
                candle(oldest, "150.000", "150.010", "149.990", "150.000"),
                candle(oldest + M1, "150.000", "150.010", "149.990", "150.000"),
            ]
        )

        assert await measure.oldest_candle(feed, now) == oldest

    @pytest.mark.asyncio
    async def test_oldest_candle_is_none_without_any_bar(self):
        now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)

        assert await measure.oldest_candle(FakeFeed(), now) is None


class TestReport:
    def results(self):
        c = candle(T0, "159.174", "159.190", "159.170", "159.180")
        return measure.score(
            [
                point(T0, "159.174"),
                point(T0, "159.186", "high", PointType.BORNE),
                point(T0, "159.190", ut=3),
            ],
            [c],
        )

    def test_compare_report_gives_every_number_the_spec_asks_for(self):
        text = measure.render_compare(
            "ctrader_icmarkets",
            "bid",
            self.results(),
            datetime(2024, 9, 30, 21, 0, tzinfo=UTC),
            datetime(2026, 9, 29, 8, 0, tzinfo=UTC),
        )

        assert "prix fourni : **bid**" in text
        assert "À 0,3 pip ou moins" in text and "Écart moyen absolu" in text
        assert "Écart max" in text
        assert "| M1 |" in text and "| M3 |" in text
        assert "2024-09-30 21:00 UTC" in text
        assert "**Non** : 67 %" in text

    def test_write_section_replaces_one_section_and_keeps_the_other(self, tmp_path):
        report = tmp_path / "mesure_sources.md"
        at = datetime(2026, 9, 29, 8, 0, tzinfo=UTC)
        measure.write_section(report, "live", "## Test du direct\n\nancien")
        measure.write_section(report, "compare", "## Écart avec OANDA\n\npremier")
        measure.write_section(report, "compare", "## Écart avec OANDA\n\nsecond")
        measure.write_section(
            report,
            "live",
            measure.render_live("x", [measure.MinuteResult(T0, 4.2)], at),
        )

        text = report.read_text(encoding="utf-8")

        assert text.startswith(measure.REPORT_TITLE)
        assert "second" in text and "premier" not in text and "ancien" not in text
        assert text.index("Écart avec OANDA") < text.index("Test du direct")
        assert "**réussi**" in text

    def test_live_report_counts_missed_minutes_and_slow_ones(self):
        minutes = [
            measure.MinuteResult(T0, 4.0),
            measure.MinuteResult(T0 + M1, 12.0),
            measure.MinuteResult(T0 + 2 * M1, None, "reseau : injoignable"),
        ]

        text = measure.render_live("ctrader_icmarkets", minutes, T0)

        assert "**échoué** : 1 minute(s) manquée(s) sur 3" in text
        assert "Minutes reçues en moins de 10 secondes : 1 sur 3" in text
        assert "reseau : injoignable" in text


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def __call__(self) -> datetime:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += timedelta(seconds=seconds)


class TestWaitForMinute:
    @pytest.mark.asyncio
    async def test_first_ask_is_at_second_3_after_the_minute(self):
        clock = FakeClock(T0 + timedelta(seconds=20))
        feed = FakeFeed([candle(T0, "1.000", "1.000", "1.000", "1.000")], now=clock)

        attempt = await wait_for_minute(feed, T0, clock=clock, sleep=clock.sleep)

        assert attempt.candle is not None
        assert attempt.delay == 3.0
        assert clock.sleeps == [43.0]

    @pytest.mark.asyncio
    async def test_polls_every_2_seconds_until_the_bar_is_there(self):
        clock = FakeClock(T0 + M1 + timedelta(seconds=3))
        feed = FakeFeed(now=clock)
        calls = 0
        history = feed.history

        async def late_history(start, end):
            nonlocal calls
            calls += 1
            if calls == 3:
                feed.candles[T0] = candle(T0, "1.000", "1.000", "1.000", "1.000")
            return await history(start, end)

        feed.history = late_history

        attempt = await wait_for_minute(feed, T0, clock=clock, sleep=clock.sleep)

        assert attempt.delay == 7.0
        assert clock.sleeps == [2.0, 2.0]

    @pytest.mark.asyncio
    async def test_gives_up_after_60_seconds_and_keeps_the_last_error(self):
        clock = FakeClock(T0 + M1)
        feed = FakeFeed(now=clock, unavailable=True)

        attempt = await wait_for_minute(feed, T0, clock=clock, sleep=clock.sleep)

        assert attempt.candle is None and attempt.delay is None
        assert attempt.last_error is not None and attempt.last_error.cause == "reseau"
        assert clock.now <= T0 + M1 + timedelta(seconds=60)
