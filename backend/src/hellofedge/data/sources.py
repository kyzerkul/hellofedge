"""Choix de la source active (`PRICE_SOURCE`, AC-8).

Le reste du code demande une `PriceFeed` ici et ne connaît jamais le fournisseur.
Ajouter une source = un adaptateur de plus et une ligne dans `open_feed`.
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from hellofedge.config import Settings
from hellofedge.data.ctrader import feed as ctrader_feed
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.protocol import host_for


class ConfigMissing(RuntimeError):
    """Un réglage nécessaire à la source manque dans l'environnement."""


def make_client(settings: Settings) -> CTraderClient:
    if settings.ctrader_client_id is None or settings.ctrader_client_secret is None:
        raise ConfigMissing(
            "CTRADER_CLIENT_ID et CTRADER_CLIENT_SECRET sont requis (page Credentials "
            "de l'application sur openapi.ctrader.com)"
        )
    return CTraderClient(
        host_for(settings.ctrader_env),
        settings.ctrader_client_id,
        settings.ctrader_client_secret.get_secret_value(),
    )


def open_feed(settings: Settings, engine: AsyncEngine) -> ctrader_feed.CTraderFeed:
    """La source nommée par `PRICE_SOURCE`, pas encore connectée."""
    if settings.price_source != ctrader_feed.SOURCE:
        raise ConfigMissing(f"PRICE_SOURCE inconnue : {settings.price_source!r}")
    if settings.ctrader_account_id is None:
        raise ConfigMissing(
            "CTRADER_ACCOUNT_ID est requis : `hellofedge feed ctrader-accounts` "
            "liste les comptes liés au jeton"
        )

    async def authorize(client: CTraderClient, account_id: int) -> None:
        await ctoken.authorize_account(engine, client, account_id)

    return ctrader_feed.CTraderFeed(
        make_client(settings),
        settings.ctrader_account_id,
        settings.ctrader_symbol,
        authorize,
    )
