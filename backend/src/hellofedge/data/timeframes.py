"""Unités de temps reconstruites depuis le M1 (fonctions pures).

Seul le M1 vient du fournisseur. Le M3 et le M5 sont calés sur l'heure pleine UTC :
:00, :03, :06… pour le M3 et :00, :05, :10… pour le M5, comme sur TradingView.
Une minute absente n'est jamais inventée : la bougie est construite avec les minutes
présentes et garde l'heure de début de sa tranche.
"""

from collections.abc import Iterable
from datetime import datetime

from hellofedge.data.candle import Candle

# Unités qui divisent l'heure : leurs tranches tombent toujours au même endroit dans
# chaque heure UTC. H4, D1 et W demandent un ancrage de session, décidé ailleurs.
SUPPORTED_MINUTES = (1, 3, 5, 15, 30, 60)


def bucket_start(ts: datetime, minutes: int) -> datetime:
    """Début de la tranche de `minutes` qui contient la minute `ts`."""
    if minutes not in SUPPORTED_MINUTES:
        raise ValueError(f"unité non gérée : {minutes} minutes")
    return ts.replace(minute=ts.minute - ts.minute % minutes, second=0, microsecond=0)


def aggregate(candles: Iterable[Candle], minutes: int) -> list[Candle]:
    """Regroupe des bougies M1 en bougies de `minutes` minutes.

    Les bougies M1 doivent être triées par heure, sans doublon.
    """
    if minutes not in SUPPORTED_MINUTES:
        raise ValueError(f"unité non gérée : {minutes} minutes")
    groups: dict[datetime, list[Candle]] = {}
    previous: datetime | None = None
    for c in candles:
        if previous is not None and c.ts_open <= previous:
            raise ValueError(
                f"bougies M1 non triées ou en double à {c.ts_open.isoformat()}"
            )
        previous = c.ts_open
        groups.setdefault(bucket_start(c.ts_open, minutes), []).append(c)
    return [_merge(start, group) for start, group in groups.items()]


def _merge(start: datetime, group: list[Candle]) -> Candle:
    volumes = [c.tick_volume for c in group if c.tick_volume is not None]
    return Candle(
        ts_open=start,
        open=group[0].open,
        high=max(c.high for c in group),
        low=min(c.low for c in group),
        close=group[-1].close,
        ask_close=group[-1].ask_close,
        tick_volume=sum(volumes) if len(volumes) == len(group) else None,
    )
