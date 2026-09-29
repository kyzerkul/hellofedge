"""Réglages lus dans l'environnement. Aucun secret dans le code."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Une variable vide (`CTRADER_ACCOUNT_ID=`, comme dans un `.env` copié depuis
    # `.env.example`) compte comme absente : la valeur par défaut s'applique, et une
    # variable obligatoire manquante le dit clairement.
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_ignore_empty=True
    )

    # Obligatoire : sans base, rien ne démarre (échec bruyant plutôt que silencieux).
    database_url: str

    log_level: str = "INFO"

    # Fichiers construits du cockpit, servis par l'api s'ils existent.
    frontend_dist: Path = Path("frontend/dist")

    # Fichier que le worker met à jour pour signaler qu'il est vivant.
    worker_heartbeat_file: Path = Path("/tmp/hellofedge-worker-heartbeat")
    worker_heartbeat_seconds: int = 15
    worker_heartbeat_max_age_seconds: int = 120

    # Documentation de l'API (/api/docs) : fermée par défaut, à ouvrir en local seulement.
    api_docs: bool = False

    # Source de prix (spec 0002). Le moteur ne lit que la source active.
    price_source: str = "ctrader_icmarkets"

    # cTrader, en lecture seule. Facultatifs ici pour que l'api démarre sans eux ;
    # le client s'arrête avec un message clair s'il lui en manque un.
    ctrader_env: Literal["demo", "live"] = "demo"
    ctrader_client_id: str | None = None
    ctrader_client_secret: SecretStr | None = None
    ctrader_account_id: int | None = None
    # Premier jeton seulement : ensuite, le dernier jeton vit dans `provider_token`.
    ctrader_access_token: SecretStr | None = None
    ctrader_refresh_token: SecretStr | None = None
    ctrader_symbol: str = "USDJPY"

    # Jours de fermeture du marché, dates fixes `MM-JJ` séparées par des virgules.
    market_holidays: str = "12-25,01-01"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
