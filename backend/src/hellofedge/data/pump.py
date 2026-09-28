"""Le flux en direct du `worker` (spec 0002, AC-4, AC-5, AC-6).

Chaque minute, à la seconde 3, on demande les bougies clôturées depuis la dernière
bougie stockée, puis toutes les 2 secondes, jusqu'à recevoir la minute qui vient de
se terminer (60 secondes au plus). Comme la demande part de la dernière bougie
stockée, un trou (coupure, redémarrage) est rattrapé tout seul :
- la minute attendue est stockée avec `backfilled = false` ;
- les minutes plus anciennes rattrapées sont stockées avec `backfilled = true`.
Chaque nouvelle bougie envoie `NOTIFY candle_m1`.

Coupures : si aucune nouvelle bougie n'arrive pendant 2 minutes, marché ouvert et hors
rollover, une coupure s'ouvre avec la cause de la dernière erreur (`donnees_absentes`
s'il n'y en a pas eu). Elle se ferme au retour des bougies (`retour_flux`, avec le
nombre de bougies rattrapées), ou à l'heure de fermeture du marché
(`fermeture_marche`). Le compte des 2 minutes repart de zéro à la réouverture et à la
fin du rollover.

Après une erreur du fournisseur, l'attente avant le nouvel essai double à chaque
échec : 2, 4, 8, 16, 32 puis 60 secondes au plus.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncEngine

from hellofedge.data import outages
from hellofedge.data.candle import M1
from hellofedge.data.feed import FeedError, PriceFeed
from hellofedge.data.live import FIRST_ASK, GIVE_UP, POLL_SECONDS, Clock, Sleep
from hellofedge.data.live import floor_minute, sleep_until
from hellofedge.data.market import MarketCalendar
from hellofedge.data.store import last_ts_open, store_candles

log = logging.getLogger("hellofedge.data.pump")

SILENCE_LIMIT = timedelta(minutes=2)
MAX_BACKOFF = 60.0
MAINTAIN_EVERY = timedelta(hours=1)


def backoff(failures: int) -> float:
    """2, 4, 8, 16, 32 puis 60 secondes au plus."""
    return min(POLL_SECONDS * 2 ** (failures - 1), MAX_BACKOFF)


class FeedPump:
    def __init__(
        self,
        engine: AsyncEngine,
        feed: PriceFeed,
        calendar: MarketCalendar,
        *,
        clock: Clock = lambda: datetime.now(UTC),
        sleep: Sleep = asyncio.sleep,
        on_tick: Callable[[], None] = lambda: None,
    ) -> None:
        self.engine = engine
        self.feed = feed
        self.calendar = calendar
        self.clock = clock
        self.sleep = sleep
        self.on_tick = on_tick
        # Dernière bougie stockée pour la source.
        self.last: datetime | None = None
        # Dernière minute traitée par la boucle.
        self.handled: datetime | None = None
        # Début du silence en cours (dernière bougie reçue, réouverture, rollover).
        self.silence_since: datetime = self.clock()
        self.failures = 0
        self.last_error: FeedError | None = None
        self.next_try_at: datetime | None = None
        self.outage: outages.OpenOutage | None = None
        self.next_maintain: datetime | None = None
        # Dernier tour de boucle : sert au fichier témoin du worker.
        self.last_tick: datetime = self.silence_since

    async def start(self) -> None:
        self.last = await last_ts_open(self.engine, self.feed.name)
        self.outage = await outages.current(self.engine, self.feed.name)
        self.silence_since = self.last_tick = self.clock()
        if self.last is None:
            log.warning(
                "aucune bougie en base : lance `hellofedge feed backfill` pour "
                "charger l'historique",
                extra={"data": {"source": self.feed.name}},
            )

    async def run(self, stop: asyncio.Event) -> None:
        await self.start()
        while not stop.is_set():
            await self.step()

    def _tick(self) -> None:
        self.last_tick = self.clock()
        self.on_tick()

    async def step(self) -> None:
        """Traite une minute : la suivante de celles déjà traitées."""
        expected = floor_minute(self.clock()) - M1
        if self.handled is not None and expected <= self.handled:
            expected = self.handled + M1
        self.handled = expected
        first_ask = expected + M1 + FIRST_ASK
        if self.next_try_at is not None and self.next_try_at > first_ask:
            first_ask = self.next_try_at
        await sleep_until(first_ask, self.clock, self.sleep)
        self._tick()
        await self._maintain()

        if not self.calendar.is_open(expected):
            await self._market_closed(expected)
            return
        if self.last is not None and self.last >= expected:
            return
        rollover = self.calendar.in_rollover(expected)
        deadline = expected + M1 + GIVE_UP
        while True:
            if await self._poll(expected):
                return
            now = self.clock()
            if rollover:
                self.silence_since = now
            else:
                await self._check_silence(now)
            delay = backoff(self.failures) if self.failures else POLL_SECONDS
            if now + timedelta(seconds=delay) > deadline:
                self.next_try_at = (
                    now + timedelta(seconds=delay) if self.failures else None
                )
                return
            await self.sleep(delay)

    async def _maintain(self) -> None:
        now = self.clock()
        if self.next_maintain is not None and now < self.next_maintain:
            return
        self.next_maintain = now + MAINTAIN_EVERY
        try:
            await self.feed.maintain()
        except FeedError as exc:
            self._failed(exc, "entretien de la source en échec")

    def _failed(self, exc: FeedError, message: str) -> None:
        self.failures += 1
        self.last_error = exc
        log.warning(
            message,
            extra={
                "data": {
                    "source": self.feed.name,
                    "cause": exc.cause,
                    "erreur": str(exc),
                }
            },
        )

    async def _poll(self, expected: datetime) -> bool:
        """Une interrogation. Vrai quand la minute attendue est en base."""
        after = self.last if self.last is not None else expected - M1
        asked_at = self.clock()
        try:
            candles = await self.feed.closed_since(after)
        except FeedError as exc:
            self._failed(exc, "interrogation du fournisseur en échec")
            return False
        self.failures = 0
        self.last_error = None
        self.next_try_at = None
        candles = [c for c in candles if c.ts_open > after]
        # Journal de chaque interrogation, pour la mesure de l'AC-4.
        log.info(
            "interrogation du fournisseur",
            extra={
                "data": {
                    "source": self.feed.name,
                    "minute": expected.isoformat(),
                    "demande": asked_at.isoformat(),
                    "bougies": len(candles),
                }
            },
        )
        if not candles:
            return False
        now = self.clock()
        late = [c for c in candles if c.ts_open < expected]
        fresh = [c for c in candles if c.ts_open >= expected]
        caught_up = await store_candles(
            self.engine, self.feed.name, late, backfilled=True, now=now, notify=True
        )
        await store_candles(
            self.engine, self.feed.name, fresh, backfilled=False, now=now, notify=True
        )
        self.last = max(candles[-1].ts_open, self.last or candles[-1].ts_open)
        self.silence_since = now
        self._tick()
        if self.outage is not None:
            await outages.close_outage(
                self.engine,
                self.outage.id,
                now,
                "retour_flux",
                len(caught_up.inserted),
            )
            log.info(
                "coupure fermée, flux revenu",
                extra={
                    "data": {
                        "source": self.feed.name,
                        "bougies_rattrapees": len(caught_up.inserted),
                    }
                },
            )
            self.outage = None
        return self.last >= expected

    async def _check_silence(self, now: datetime) -> None:
        if self.outage is not None or now - self.silence_since < SILENCE_LIMIT:
            return
        cause = self.last_error.cause if self.last_error else "donnees_absentes"
        self.outage = await outages.open_outage(self.engine, self.feed.name, now, cause)
        log.error(
            "coupure du flux de prix",
            extra={"data": {"source": self.feed.name, "cause": self.outage.cause}},
        )

    async def _market_closed(self, minute: datetime) -> None:
        self.silence_since = self.clock()
        if self.outage is None:
            return
        closed_at = self.calendar.closed_at(minute)
        await outages.close_outage(
            self.engine,
            self.outage.id,
            max(closed_at, self.outage.started_at),
            "fermeture_marche",
        )
        log.info(
            "coupure fermée à la fermeture du marché",
            extra={"data": {"source": self.feed.name}},
        )
        self.outage = None
