from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from hellofedge.data.candle import Candle
from hellofedge.data.timeframes import aggregate, bucket_start

START = datetime(2026, 9, 22, 8, 58, tzinfo=UTC)


def m1(minute: int, o: str, h: str, low: str, c: str, volume: int | None = 1) -> Candle:
    return Candle(
        ts_open=START + timedelta(minutes=minute),
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(low),
        close=Decimal(c),
        tick_volume=volume,
    )


# 08:58 à 09:06 UTC, une minute chacune.
SERIES = [
    m1(0, "157.230", "157.240", "157.220", "157.235"),  # 08:58
    m1(1, "157.235", "157.250", "157.230", "157.245"),  # 08:59
    m1(2, "157.245", "157.260", "157.200", "157.210"),  # 09:00
    m1(3, "157.210", "157.300", "157.205", "157.290"),  # 09:01
    m1(4, "157.290", "157.295", "157.250", "157.260"),  # 09:02
    m1(5, "157.260", "157.270", "157.240", "157.250"),  # 09:03
    m1(6, "157.250", "157.255", "157.100", "157.120"),  # 09:04
    m1(7, "157.120", "157.130", "157.110", "157.125"),  # 09:05
    m1(8, "157.125", "157.140", "157.120", "157.135"),  # 09:06
]


def at(hour: int, minute: int) -> datetime:
    return datetime(2026, 9, 22, hour, minute, tzinfo=UTC)


def test_m3_is_aligned_on_00_03_06():
    bars = aggregate(SERIES, 3)

    assert [b.ts_open for b in bars] == [at(8, 57), at(9, 0), at(9, 3), at(9, 6)]
    first_full = bars[1]  # 09:00, 09:01, 09:02
    assert first_full.open == Decimal("157.245")
    assert first_full.high == Decimal("157.300")
    assert first_full.low == Decimal("157.200")
    assert first_full.close == Decimal("157.260")
    assert first_full.tick_volume == 3


def test_m5_is_aligned_on_00_05():
    bars = aggregate(SERIES, 5)

    assert [b.ts_open for b in bars] == [at(8, 55), at(9, 0), at(9, 5)]
    full = bars[1]  # 09:00 à 09:04
    assert (full.open, full.high, full.low, full.close) == (
        Decimal("157.245"),
        Decimal("157.300"),
        Decimal("157.100"),
        Decimal("157.120"),
    )


def test_a_missing_minute_is_not_invented():
    without_0901 = [c for c in SERIES if c.ts_open != at(9, 1)]

    bar = aggregate(without_0901, 3)[1]

    assert bar.ts_open == at(9, 0)
    assert bar.high == Decimal("157.295")  # le plus haut de 09:01 a disparu avec elle
    assert bar.tick_volume == 2


def test_the_bucket_keeps_its_start_time_when_its_first_minute_is_missing():
    without_0900 = [c for c in SERIES if c.ts_open != at(9, 0)]

    bar = aggregate(without_0900, 3)[1]

    assert bar.ts_open == at(9, 0)
    assert bar.open == Decimal("157.210")  # ouverture de la première minute présente


def test_volume_is_unknown_when_one_minute_has_none():
    series = [
        m1(2, "157.245", "157.260", "157.200", "157.210", volume=None),
        *SERIES[3:5],
    ]

    assert aggregate(series, 3)[0].tick_volume is None


def test_m1_aggregation_returns_the_same_candles():
    assert aggregate(SERIES, 1) == SERIES


def test_refuses_unsorted_or_duplicated_minutes():
    with pytest.raises(ValueError, match="non triées ou en double"):
        aggregate([SERIES[1], SERIES[0]], 3)
    with pytest.raises(ValueError, match="non triées ou en double"):
        aggregate([SERIES[0], SERIES[0]], 3)


@pytest.mark.parametrize("minutes", [2, 4, 7, 240])
def test_refuses_units_that_do_not_divide_the_hour(minutes):
    with pytest.raises(ValueError, match="unité non gérée"):
        aggregate(SERIES, minutes)


def test_bucket_start():
    assert bucket_start(at(12, 38), 3) == at(12, 36)
    assert bucket_start(at(13, 34), 5) == at(13, 30)
    assert bucket_start(at(13, 30), 5) == at(13, 30)
