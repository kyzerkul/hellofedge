"""Interface commune des sources de prix (spec 0002).

Une source ne fait que **lire** des bougies M1 : aucune fonction ne passe, ne modifie
ou n'annule quoi que ce soit chez le fournisseur. Le reste du code ne dépend que de
cette interface, jamais d'un fournisseur précis.
"""

from datetime import datetime
from typing import Literal, Protocol

from hellofedge.data.candle import Candle, PriceKind


class FeedError(Exception):
    """Erreur d'une source. `cause` est la valeur écrite dans `feed_outage.cause`."""

    cause: str = "erreur_api"


class FeedAuthError(FeedError):
    """Clé ou jeton refusé par le fournisseur."""

    cause = "auth"


class FeedRateLimited(FeedError):
    """Le fournisseur limite le nombre d'appels : il faut attendre avant de réessayer."""

    cause = "limite_api"


class FeedUnavailable(FeedError):
    """Fournisseur injoignable : réseau (connexion, DNS), réponse 5xx ou délai dépassé."""

    def __init__(
        self,
        message: str,
        cause: Literal["reseau", "erreur_api", "timeout"] = "reseau",
    ) -> None:
        super().__init__(message)
        self.cause = cause


class PriceFeed(Protocol):
    """Une source de bougies M1 USD/JPY, en lecture seule."""

    # Identifiant stocké dans `candle_m1.source` (`fxcm`, `finnhub_oanda`, `dukascopy`…).
    name: str
    # Prix fourni par la source : bid, ou mid si elle ne donne rien d'autre.
    price_kind: PriceKind

    async def history(self, start: datetime, end: datetime) -> list[Candle]:
        """Bougies M1 de `start` (inclus) à `end` (exclu), deux heures UTC.

        Triées, datées à l'ouverture de leur minute, en UTC, sans doublon.
        """
        ...

    async def closed_since(self, after: datetime) -> list[Candle]:
        """Bougies M1 **clôturées** qui s'ouvrent après `after`.

        Liste vide si la minute attendue n'est pas encore disponible chez le fournisseur.
        """
        ...
