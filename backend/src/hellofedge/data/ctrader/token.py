"""Jeton cTrader (AC-13) : le dernier jeton valable vit dans `provider_token`.

Règles de la spec 0002 :
- Le premier jeton vient de l'environnement (`CTRADER_ACCESS_TOKEN`,
  `CTRADER_REFRESH_TOKEN`). Sa date de fin est inconnue : on le note comme expirant
  dans `SEED_LIFETIME`, sous le seuil de renouvellement, pour que le `worker` le
  renouvelle dès son premier passage et reçoive la vraie date de cTrader. Les
  commandes ponctuelles peuvent s'en servir tout de suite.
- **Seul le `worker` renouvelle**, sous son propre verrou PostgreSQL (distinct du
  verrou « un seul worker »), tenu le temps du renouvellement. Renouveler invalide
  l'ancien jeton : le nouveau est écrit en base avant d'être utilisé.
- Les commandes ponctuelles ne renouvellent jamais. S'il reste moins de
  `COMMAND_MIN_VALIDITY`, elles s'arrêtent avec un message clair.
- Sur un refus d'authentification, on relit la base et on réessaie une fois. De même
  pour un refus du renouvellement : le verrou est relâché, puis repris, pour qu'un
  `--reseed` en attente passe d'abord.
- `--reseed` prend le même verrou que le renouvellement avant d'écrire.

Aucun jeton n'apparaît jamais dans un journal ni dans un message d'erreur.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from hellofedge.config import Settings
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.protocol import ALREADY_LOGGED_IN, Msg
from hellofedge.data.feed import FeedAuthError, FeedError
from hellofedge.data.models import ProviderToken

log = logging.getLogger("hellofedge.data.ctrader")

SOURCE = "ctrader_icmarkets"

# Renouveler quand il reste moins de 7 jours.
RENEW_BEFORE = timedelta(days=7)
# Durée supposée du premier jeton : sous RENEW_BEFORE, au dessus de COMMAND_MIN_VALIDITY.
SEED_LIFETIME = timedelta(days=6)
# Une commande ponctuelle refuse un jeton qui expire dans moins d'un jour.
COMMAND_MIN_VALIDITY = timedelta(days=1)

# Clé du verrou de renouvellement : les octets ASCII de « HF-TOKEN ».
# Distincte de WORKER_LOCK_KEY (spec 0001), sinon les deux se bloqueraient.
TOKEN_LOCK_KEY = 0x48462D544F4B454E

# Écriture du jeton renouvelé : essais et attente entre deux essais (secondes).
SAVE_ATTEMPTS = 5
SAVE_RETRY_SECONDS = 2.0

RUNBOOK = (
    "régénère le jeton dans le Sandbox cTrader (portée accounts), mets-le dans "
    "CTRADER_ACCESS_TOKEN et CTRADER_REFRESH_TOKEN, puis lance "
    "`hellofedge feed ctrader-token --reseed`"
)


class TokenMissing(RuntimeError):
    """Aucun jeton en base ni dans l'environnement."""


class TokenExpiringSoon(RuntimeError):
    """Le jeton expire trop tôt pour une commande ponctuelle, qui ne renouvelle jamais."""


@dataclass(frozen=True)
class Token:
    access_token: str
    refresh_token: str
    expires_at: datetime

    def __repr__(self) -> str:
        # Jamais le jeton lui-même, même dans une trace d'erreur.
        return f"Token(expires_at={self.expires_at!r})"


def env_token(settings: Settings, now: datetime) -> Token:
    """Le premier jeton, lu dans l'environnement."""
    if settings.ctrader_access_token is None or settings.ctrader_refresh_token is None:
        raise TokenMissing(
            "CTRADER_ACCESS_TOKEN et CTRADER_REFRESH_TOKEN sont requis pour le "
            "premier jeton cTrader"
        )
    return Token(
        settings.ctrader_access_token.get_secret_value(),
        settings.ctrader_refresh_token.get_secret_value(),
        now + SEED_LIFETIME,
    )


@asynccontextmanager
async def token_lock(engine: AsyncEngine) -> AsyncIterator[None]:
    """Verrou du jeton, pris par le renouvellement et par `--reseed`.

    PostgreSQL sert les demandes en attente dans l'ordre : qui relâche puis reprend
    le verrou passe après celles qui attendaient déjà.
    """
    async with engine.connect() as lock_conn:
        await lock_conn.execute(
            text("SELECT pg_advisory_lock(:k)"), {"k": TOKEN_LOCK_KEY}
        )
        await lock_conn.commit()
        try:
            yield
        finally:
            await lock_conn.execute(
                text("SELECT pg_advisory_unlock(:k)"), {"k": TOKEN_LOCK_KEY}
            )
            await lock_conn.commit()


async def load(engine: AsyncEngine) -> Token | None:
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(
                    ProviderToken.access_token,
                    ProviderToken.refresh_token,
                    ProviderToken.expires_at,
                ).where(ProviderToken.source == SOURCE)
            )
        ).first()
    return (
        None
        if row is None
        else Token(row.access_token, row.refresh_token, row.expires_at)
    )


async def _write(
    engine: AsyncEngine, token: Token, now: datetime, *, replace: bool
) -> None:
    values = {
        "source": SOURCE,
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "expires_at": token.expires_at,
        "updated_at": now,
    }
    stmt = insert(ProviderToken).values(**values)
    if replace:
        stmt = stmt.on_conflict_do_update(
            index_elements=[ProviderToken.source],
            set_={k: v for k, v in values.items() if k != "source"},
        )
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=[ProviderToken.source])
    async with engine.begin() as conn:
        await conn.execute(stmt)


async def ensure_seeded(
    engine: AsyncEngine, settings: Settings, now: datetime
) -> Token:
    """Le jeton en base. S'il n'y en a pas encore, on l'initialise depuis l'environnement."""
    token = await load(engine)
    if token is not None:
        return token
    await _write(engine, env_token(settings, now), now, replace=False)
    log.info("jeton cTrader initialisé depuis l'environnement")
    token = await load(engine)
    assert token is not None
    return token


async def reseed(engine: AsyncEngine, settings: Settings, now: datetime) -> Token:
    """Remplace le jeton en base par celui de l'environnement (après une régénération manuelle).

    Attend la fin d'un renouvellement en cours : ni l'un ni l'autre n'écrase l'autre
    à son insu, et la ligne finale est celle du `--reseed`.
    """
    token = env_token(settings, now)
    async with token_lock(engine):
        await _write(engine, token, now, replace=True)
    log.info("jeton cTrader remplacé par celui de l'environnement")
    return token


async def token_for_command(
    engine: AsyncEngine, settings: Settings, now: datetime
) -> Token:
    """Jeton pour une commande ponctuelle : jamais renouvelé ici."""
    token = await ensure_seeded(engine, settings, now)
    if token.expires_at - now < COMMAND_MIN_VALIDITY:
        raise TokenExpiringSoon(
            "le jeton cTrader expire dans moins d'un jour : laisse le worker le "
            "renouveler, ou " + RUNBOOK
        )
    return token


async def _save_renewed(
    engine: AsyncEngine,
    token: Token,
    now: datetime,
    sleep: Callable[[float], Awaitable[None]],
) -> None:
    """Écrit le jeton renouvelé. L'ancien est déjà invalide : on insiste avant d'abandonner."""
    for attempt in range(1, SAVE_ATTEMPTS + 1):
        try:
            await _write(engine, token, now, replace=True)
            return
        except Exception as exc:  # noqa: BLE001 : toute erreur de base, le jeton est en mémoire
            log.warning(
                "écriture du jeton cTrader renouvelé impossible",
                extra={"data": {"essai": attempt, "erreur": type(exc).__name__}},
            )
            if attempt < SAVE_ATTEMPTS:
                await sleep(SAVE_RETRY_SECONDS * attempt)
    log.error("jeton cTrader renouvelé perdu : %s", RUNBOOK)
    raise FeedAuthError("jeton cTrader renouvelé mais non enregistré : " + RUNBOOK)


async def refresh_if_needed(
    engine: AsyncEngine,
    client: CTraderClient,
    settings: Settings,
    now: datetime,
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Token:
    """Renouvelle le jeton s'il reste moins de `RENEW_BEFORE`. Réservé au `worker`.

    `client` doit être connecté (application authentifiée). Sur un refus du
    renouvellement, on relâche le verrou, on le reprend et on relit la base : si un
    `--reseed` a posé un jeton qui n'a plus besoin d'être renouvelé, on s'arrête là,
    sinon on réessaie une fois avec le jeton relu. Le second refus remonte
    (`FeedAuthError`, coupure `auth`).
    """
    await ensure_seeded(engine, settings, now)
    for attempt in (1, 2):
        async with token_lock(engine):
            # Relu sous le verrou : un autre passage ou un `--reseed` vient peut-être
            # de le remplacer.
            current = await load(engine)
            assert current is not None
            if current.expires_at - now >= RENEW_BEFORE:
                return current
            try:
                payload = await client.request(
                    Msg.REFRESH_TOKEN_REQ, {"refreshToken": current.refresh_token}
                )
            except FeedAuthError:
                if attempt == 2:
                    raise
                log.warning(
                    "renouvellement du jeton cTrader refusé, nouvel essai avec le "
                    "jeton relu en base"
                )
                continue
            renewed = Token(
                str(payload["accessToken"]),
                str(payload["refreshToken"]),
                now + timedelta(seconds=int(payload["expiresIn"])),
            )
            await _save_renewed(engine, renewed, now, sleep)
            log.info(
                "jeton cTrader renouvelé",
                extra={"data": {"expires_at": renewed.expires_at.isoformat()}},
            )
            return renewed
    raise AssertionError("inaccessible")


async def authorize_account(
    engine: AsyncEngine, client: CTraderClient, account_id: int
) -> None:
    """Authentifie le compte sur la connexion avec le jeton en base.

    Sur un refus, on relit la base (le jeton vient peut-être d'être renouvelé) et on
    réessaie une fois. Le second refus remonte (`FeedAuthError`, coupure `auth`).
    """
    for attempt in (1, 2):
        token = await load(engine)
        if token is None:
            raise TokenMissing("aucun jeton cTrader en base")
        try:
            await client.request(
                Msg.ACCOUNT_AUTH_REQ,
                {"ctidTraderAccountId": account_id, "accessToken": token.access_token},
            )
        except FeedError as exc:
            if exc.error_code == ALREADY_LOGGED_IN:
                break
            if not isinstance(exc, FeedAuthError) or attempt == 2:
                raise
            log.warning(
                "compte cTrader refusé, nouvel essai avec le jeton relu en base"
            )
            continue
        break
    client.authorized_account = account_id
