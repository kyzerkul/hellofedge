from pathlib import Path

import pytest
from pydantic import ValidationError

from hellofedge.config import Settings, get_settings


def test_refuses_to_start_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)


def test_reads_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")

    assert get_settings().database_url == "postgresql://u:p@h/db"


def test_uses_safe_defaults_when_only_database_url_is_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    for name in (
        "LOG_LEVEL",
        "FRONTEND_DIST",
        "WORKER_HEARTBEAT_FILE",
        "WORKER_HEARTBEAT_SECONDS",
        "WORKER_HEARTBEAT_MAX_AGE_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"
    assert settings.frontend_dist == Path("frontend/dist")
    assert settings.worker_heartbeat_seconds == 15
    assert settings.worker_heartbeat_max_age_seconds == 120


def test_converts_numeric_and_path_variables_from_text(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("WORKER_HEARTBEAT_SECONDS", "5")
    monkeypatch.setenv("WORKER_HEARTBEAT_FILE", str(tmp_path / "hb"))

    settings = Settings(_env_file=None)

    assert settings.worker_heartbeat_seconds == 5
    assert settings.worker_heartbeat_file == tmp_path / "hb"


def test_rejects_a_non_numeric_heartbeat_interval(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("WORKER_HEARTBEAT_SECONDS", "souvent")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
