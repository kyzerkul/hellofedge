"""Processus `worker` : flux de prix, moteur, planificateur et alertes.

Une seule copie à la fois. Au démarrage, le worker prend un verrou PostgreSQL
(advisory lock) et le garde tant qu'il tourne. Une seconde copie qui ne l'obtient
pas s'arrête, ce qui empêche les alertes en double.

Santé : le worker met à jour un fichier témoin. Pour l'instant il le touche à chaque
tour de boucle. Quand le flux de prix arrivera (scope n°2), il le touchera à chaque
bougie reçue, pour que « vivant » veuille dire « reçoit des prix ».

Lancement : `hellofedge-worker`. Contrôle de santé : `hellofedge-worker --check`.
"""

import asyncio
import logging
import signal
import sys
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from hellofedge.config import Settings, get_settings
from hellofedge.db import make_engine
from hellofedge.logs import setup_logging

log = logging.getLogger("hellofedge.worker")

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


async def run(settings: Settings) -> None:
    engine = make_engine(settings.database_url)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    try:
        async with engine.connect() as lock_conn:
            await acquire_worker_lock(lock_conn)
            log.info("worker démarré, verrou obtenu")
            while not stop.is_set():
                # Vérifie que la connexion qui porte le verrou est toujours vivante.
                await lock_conn.execute(text("SELECT 1"))
                await lock_conn.commit()
                touch_heartbeat(settings)
                try:
                    await asyncio.wait_for(
                        stop.wait(), timeout=settings.worker_heartbeat_seconds
                    )
                except TimeoutError:
                    pass
            log.info("worker arrêté proprement")
    finally:
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
    except LockNotAcquired as exc:
        log.error("arrêt : %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
