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


def test_a_env_copied_from_env_example_starts_with_defaults(monkeypatch, tmp_path):
    # Revue du 2026-09-29, major 2 : les lignes vides de `.env.example` ne cassent
    # rien et n'écrasent pas les valeurs par défaut.
    example = Path(__file__).resolve().parents[2] / ".env.example"
    env = tmp_path / ".env"
    env.write_text(
        example.read_text(encoding="utf-8").replace(
            "DATABASE_URL=\n", "DATABASE_URL=postgresql://u:p@h/db\n"
        ),
        encoding="utf-8",
    )
    for line in example.read_text(encoding="utf-8").splitlines():
        name = line.split("=", 1)[0].strip()
        if name and not name.startswith("#"):
            monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=env)

    assert settings.ctrader_account_id is None
    assert settings.ctrader_client_id is None
    assert settings.market_holidays == "12-25,01-01"
    assert settings.price_source == "ctrader_icmarkets"


def test_empty_variables_count_as_absent(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("CTRADER_ACCOUNT_ID", "")
    monkeypatch.setenv("CTRADER_CLIENT_ID", "")
    monkeypatch.setenv("MARKET_HOLIDAYS", "")

    settings = Settings(_env_file=None)

    assert settings.ctrader_account_id is None
    assert settings.ctrader_client_id is None
    assert settings.market_holidays == "12-25,01-01"


def test_an_empty_database_url_is_still_required(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)
