"""Les migrations se lancent à part (`alembic upgrade head`), jamais au démarrage des processus."""

import os
import subprocess
import sys
from pathlib import Path

import psycopg

BACKEND = Path(__file__).resolve().parents[1]


def alembic(*args: str, database_url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_upgrade_head_runs_against_a_real_database(db_url):
    result = alembic("upgrade", "head", database_url=db_url)

    assert result.returncode == 0, result.stderr
    with psycopg.connect(db_url) as conn:
        found = conn.execute("SELECT to_regclass('public.alembic_version')").fetchone()
    assert found is not None and found[0] == "alembic_version"


def test_upgrade_head_can_run_twice_without_error(db_url):
    alembic("upgrade", "head", database_url=db_url)

    result = alembic("upgrade", "head", database_url=db_url)

    assert result.returncode == 0, result.stderr


def test_offline_mode_writes_sql_without_touching_a_database():
    result = alembic(
        "upgrade", "head", "--sql", database_url="postgresql://u:p@127.0.0.1:1/db"
    )

    assert result.returncode == 0, result.stderr
    # Pas encore de migration écrite (scope n°4) : le script SQL est une transaction vide.
    assert "BEGIN;" in result.stdout


def test_the_database_url_never_comes_from_alembic_ini():
    ini = (BACKEND / "alembic.ini").read_text(encoding="utf-8")

    assert not any(
        line.strip().startswith("sqlalchemy.url") for line in ini.splitlines()
    )
