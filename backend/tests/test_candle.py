from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from hellofedge.data.candle import Candle, check_utc_minute

T = datetime(2026, 8, 24, 10, 47, tzinfo=UTC)


def candle(**kw) -> Candle:
    base = {
        "ts_open": T,
        "open": Decimal("159.174"),
        "high": Decimal("159.186"),
        "low": Decimal("159.170"),
        "close": Decimal("159.184"),
    }
    return Candle(**(base | kw))


def test_accepts_a_consistent_m1_bid_candle():
    c = candle(ask_close=Decimal("159.192"), tick_volume=42)

    assert c.close - c.open == Decimal("0.010")
    assert c.ts_open == T


def test_keeps_a_tenth_of_a_pip_exact():
    c = candle(low=Decimal("159.172"))

    assert c.open - c.low == Decimal("0.002")


@pytest.mark.parametrize(
    "ts",
    [
        datetime(2026, 8, 24, 10, 47),  # sans fuseau
        datetime(2026, 8, 24, 10, 47, tzinfo=timezone(timedelta(hours=1))),
        datetime(2026, 8, 24, 10, 47, 30, tzinfo=UTC),
    ],
)
def test_refuses_a_time_that_is_not_a_full_utc_minute(ts):
    with pytest.raises(ValueError):
        candle(ts_open=ts)


def test_normalises_an_equivalent_utc_zone_to_utc():
    c = candle(ts_open=T.astimezone(timezone(timedelta(0))))

    assert c.ts_open.tzinfo is UTC


def test_refuses_floats():
    with pytest.raises(TypeError, match="Decimal"):
        candle(open=159.174)


def test_refuses_more_than_three_decimals():
    with pytest.raises(ValueError, match="3 décimales"):
        candle(close=Decimal("159.1845"))


@pytest.mark.parametrize(
    "kw",
    [
        {"high": Decimal("159.180")},  # plus haut sous la clôture
        {"low": Decimal("159.175")},  # plus bas au-dessus de l'ouverture
    ],
)
def test_refuses_an_inconsistent_candle(kw):
    with pytest.raises(ValueError, match="incohérente"):
        candle(**kw)


def test_check_utc_minute_accepts_a_full_minute():
    check_utc_minute(T)
