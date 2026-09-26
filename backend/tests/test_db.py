import pytest
from sqlalchemy import text

from hellofedge.db import async_url, make_engine


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
        ("postgresql://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
        ("postgresql+psycopg://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
    ],
)
def test_async_url_always_selects_the_psycopg_driver(given, expected):
    assert async_url(given) == expected


def test_async_url_leaves_an_unknown_scheme_untouched():
    assert async_url("sqlite:///x.db") == "sqlite:///x.db"


def test_async_url_keeps_query_parameters():
    assert (
        async_url("postgresql://u:p@h/db?sslmode=require")
        == "postgresql+psycopg://u:p@h/db?sslmode=require"
    )


@pytest.mark.asyncio
async def test_every_connection_works_in_utc(db_url):
    # Règle du projet : heures stockées et calculées en UTC, quel que soit le réglage du serveur.
    engine = make_engine(db_url)
    try:
        async with engine.connect() as conn:
            tz = (await conn.execute(text("SHOW TimeZone"))).scalar_one()
    finally:
        await engine.dispose()

    assert tz == "UTC"
