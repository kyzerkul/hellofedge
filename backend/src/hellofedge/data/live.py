"""Lecture d'une minute clôturée en direct (spec 0002, *Decision*).

À la seconde 3 de chaque minute, on demande la bougie M1 qui vient de se terminer,
par la même requête que l'historique, puis toutes les 2 secondes jusqu'à ce qu'elle
soit disponible, pendant 60 secondes au plus. Le rejeu et le direct lisent ainsi
exactement la même bougie.

Utilisé par `hellofedge feed live-test`, puis par la boucle du `worker`.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from hellofedge.data.candle import M1, Candle
from hellofedge.data.feed import FeedError, PriceFeed

log = logging.getLogger("hellofedge.data.live")

FIRST_ASK = timedelta(seconds=3)
POLL_SECONDS = 2.0
GIVE_UP = timedelta(seconds=60)

Clock = Callable[[], datetime]
Sleep = Callable[[float], Awaitable[None]]


@dataclass(frozen=True)
class Attempt:
    """Ce que l'attente d'une minute a donné."""

    ts_open: datetime
    candle: Candle | None
    # Secondes entre la fin de la minute et la réception ; None si rien n'est venu.
    delay: float | None
    # Dernière erreur du fournisseur pendant l'attente, s'il y en a eu une.
    last_error: FeedError | None


def floor_minute(ts: datetime) -> datetime:
    return ts.astimezone(UTC).replace(second=0, microsecond=0)


async def sleep_until(when: datetime, clock: Clock, sleep: Sleep) -> None:
    wait = (when - clock()).total_seconds()
    if wait > 0:
        await sleep(wait)


async def wait_for_minute(
    feed: PriceFeed,
    ts_open: datetime,
    *,
    clock: Clock = lambda: datetime.now(UTC),
    sleep: Sleep = asyncio.sleep,
) -> Attempt:
    """Attend la bougie M1 de `ts_open` : première demande à fin + 3 s, puis toutes
    les 2 s, abandon 60 s après la fin de la minute."""
    end = ts_open + M1
    deadline = end + GIVE_UP
    await sleep_until(end + FIRST_ASK, clock, sleep)
    last_error: FeedError | None = None
    while True:
        asked_at = clock()
        try:
            candles = await feed.closed_since(ts_open - M1)
        except FeedError as exc:
            last_error = exc
            candles = []
            log.warning(
                "interrogation du fournisseur en échec",
                extra={"data": {"minute": ts_open.isoformat(), "cause": exc.cause}},
            )
        found = next((c for c in candles if c.ts_open == ts_open), None)
        received_at = clock()
        # Journal de chaque interrogation, pour la mesure de l'AC-4.
        log.info(
            "interrogation du fournisseur",
            extra={
                "data": {
                    "minute": ts_open.isoformat(),
                    "demande": asked_at.isoformat(),
                    "trouvee": found is not None,
                }
            },
        )
        if found is not None:
            return Attempt(
                ts_open, found, (received_at - end).total_seconds(), last_error
            )
        if received_at + timedelta(seconds=POLL_SECONDS) > deadline:
            return Attempt(ts_open, None, None, last_error)
        await sleep(POLL_SECONDS)
