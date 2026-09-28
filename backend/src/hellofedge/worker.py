"""Processus `worker` : flux de prix, moteur, planificateur et alertes.

Une seule copie à la fois. Au démarrage, le worker prend un verrou PostgreSQL
(advisory lock) et le garde tant qu'il tourne. Une seconde copie qui ne l'obtient
pas s'arrête, ce qui empêche les alertes en double.

Flux de prix (spec 0002) : la boucle `FeedPump` lit chaque minute clôturée de la
source active, rattrape les trous et ouvre ou ferme les coupures. Elle renouvelle
aussi le jeton cTrader (seul le worker le fait). Sans réglages cTrader, le worker
tourne sans flux et le dit dans son journal.

Santé : le worker met à jour un fichier témoin tant que sa connexion à la base répond
et que la boucle du flux tourne (un tour par minute, marché ouvert ou fermé). Une
panne du fournisseur n'arrête pas la boucle : elle ouvre une coupure `feed_outage`.

Lancement : `hellofedge-worker`. Contrôle de santé : `hellofedge-worker --check`.
"""

import asyncio
import contextlib
import logging
import signal
import sys
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from hellofedge.config import Settings, get_settings
from hellofedge.data.market import MarketCalendar, parse_holidays
from hellofedge.data.pump import FeedPump
from hellofedge.data.sources import ConfigMissing, open_feed
from hellofedge.db import make_engine
from hellofedge.logs import setup_logging

log = logging.getLogger("hellofedge.worker")

# La boucle du flux fait un tour par minute : au delà, elle est considérée bloquée.
PUMP_STALL = timedelta(seconds=150)

# Clé du verrou « un seul worker » : les octets ASCII de « HELLOFED ».
WORKER_LOCK_KEY = 0x48454C4C4F464544


class LockNotAcquired(RuntimeError):
    pass


async def acquire_worker_lock(conn: AsyncConnection) -> None:
    got = (
        await conn.execute(
            text("SELECT pg_try_advisory_lock(:k)"), {"k": WORKER_LOCK_KEY}
        )
    ).scalar_one()
    # Valider la transaction implicite : le verrou de session reste tenu, la connexion n'est pas bloquée.
    await conn.commit()
    if not got:
        raise LockNotAcquired("un autre worker tient déjà le verrou")


def touch_heartbeat(settings: Settings) -> None:
    settings.worker_heartbeat_file.write_text(str(time.time()))


class PumpFailed(RuntimeError):
    pass


def make_pump(settings: Settings, engine: AsyncEngine) -> FeedPump | None:
    try:
        feed = open_feed(settings, engine, renew_token=True)
    except ConfigMissing as exc:
        log.warning(
            "source de prix non configurée, le worker tourne sans flux : %s", exc
        )
        return None
    return FeedPump(
        engine, feed, MarketCalendar(parse_holidays(settings.market_holidays))
    )


async def run(settings: Settings) -> None:
    engine = make_engine(settings.database_url)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    pump: FeedPump | None = None
    pump_task: asyncio.Task[None] | None = None
    try:
        async with engine.connect() as lock_conn:
            await acquire_worker_lock(lock_conn)
            log.info("worker démarré, verrou obtenu")
            pump = make_pump(settings, engine)
            if pump is not None:
                pump_task = asyncio.create_task(pump.run(stop))
            while not stop.is_set():
                # Vérifie que la connexion qui porte le verrou est toujours vivante.
                await lock_conn.execute(text("SELECT 1"))
                await lock_conn.commit()
                if pump_task is not None and pump_task.done():
                    exc = pump_task.exception() if not pump_task.cancelled() else None
                    raise PumpFailed(f"la boucle du flux s'est arrêtée : {exc!r}")
                if pump is None or datetime.now(UTC) - pump.last_tick < PUMP_STALL:
                    touch_heartbeat(settings)
                try:
                    await asyncio.wait_for(
                        stop.wait(), timeout=settings.worker_heartbeat_seconds
                    )
                except TimeoutError:
                    pass
            log.info("worker arrêté proprement")
    finally:
        if pump_task is not None:
            pump_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await pump_task
        if pump is not None:
            await pump.feed.aclose()
        await engine.dispose()


def check(settings: Settings) -> int:
    """Code 0 si le fichier témoin est récent, 1 sinon (utilisé par le healthcheck Docker)."""
    try:
        age = time.time() - float(settings.worker_heartbeat_file.read_text())
    except (OSError, ValueError):
        return 1
    return 0 if age <= settings.worker_heartbeat_max_age_seconds else 1


def main() -> None:
    settings = get_settings()
    if "--check" in sys.argv[1:]:
        sys.exit(check(settings))
    setup_logging(settings.log_level)
    try:
        asyncio.run(run(settings))
    except (LockNotAcquired, PumpFailed) as exc:
        log.error("arrêt : %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
