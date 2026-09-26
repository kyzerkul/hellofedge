"""Bougie M1 bid : la seule forme de prix que le reste du code connaît.

Les prix sont des Decimal à 3 décimales au plus (NUMERIC(10,3) en base), jamais des
nombres à virgule flottante : 0,2 pip doit rester exactement 0.002.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

M1 = timedelta(minutes=1)


class PriceKind(StrEnum):
    """Prix fourni par une source : bid (celui du graphique du trader) ou mid."""

    BID = "bid"
    MID = "mid"


def check_utc_minute(ts: datetime) -> None:
    """Refuse une heure qui n'est pas une minute pleine en UTC."""
    if ts.tzinfo is None or ts.utcoffset() != timedelta(0):
        raise ValueError(f"heure non UTC : {ts!r}")
    if ts.second or ts.microsecond:
        raise ValueError(f"heure qui n'est pas une minute pleine : {ts.isoformat()}")


def _check_price(name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} doit être un Decimal, reçu {type(value).__name__}")
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{name} invalide : {value}")
    exponent = value.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -3:
        raise ValueError(f"{name} a plus de 3 décimales : {value}")


@dataclass(frozen=True, slots=True)
class Candle:
    """Une bougie datée à l'ouverture de sa période, en UTC.

    Pour une bougie M1, `ts_open` est la minute pleine d'ouverture. Pour une bougie
    reconstruite (M3, M5…), c'est le début de sa tranche (:00, :03, :06…).
    """

    ts_open: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    ask_close: Decimal | None = None
    tick_volume: int | None = None

    def __post_init__(self) -> None:
        check_utc_minute(self.ts_open)
        for name in ("open", "high", "low", "close"):
            _check_price(name, getattr(self, name))
        if self.ask_close is not None:
            _check_price("ask_close", self.ask_close)
        if self.low > min(self.open, self.close) or self.high < max(
            self.open, self.close
        ):
            raise ValueError(
                f"bougie incohérente à {self.ts_open.isoformat()} : "
                f"O={self.open} H={self.high} L={self.low} C={self.close}"
            )
        if self.tick_volume is not None and self.tick_volume < 0:
            raise ValueError(f"tick_volume négatif : {self.tick_volume}")
        # Toujours ramener l'heure à UTC lui-même, quel que soit l'objet fuseau reçu.
        object.__setattr__(self, "ts_open", self.ts_open.astimezone(UTC))
