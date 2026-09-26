"""Réglages lus dans l'environnement. Aucun secret dans le code."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Obligatoire : sans base, rien ne démarre (échec bruyant plutôt que silencieux).
    database_url: str

    log_level: str = "INFO"

    # Fichiers construits du cockpit, servis par l'api s'ils existent.
    frontend_dist: Path = Path("frontend/dist")

    # Fichier que le worker met à jour pour signaler qu'il est vivant.
    worker_heartbeat_file: Path = Path("/tmp/hellofedge-worker-heartbeat")
    worker_heartbeat_seconds: int = 15
    worker_heartbeat_max_age_seconds: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
