"""Outils partagés des tests.

Les tests qui ont besoin d'une vraie base PostgreSQL lisent TEST_DATABASE_URL
(une base jetable, jamais celle de production). Sans elle, ils sont sautés.
"""

import logging
import os

import pytest
import pytest_asyncio
from fake_ctrader import FakeCTrader
from sqlalchemy import text
from test_migrations import alembic

from hellofedge import cli
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.feed import CTraderFeed
from hellofedge.db import make_engine

from hellofedge.config import get_settings


@pytest.fixture
def db_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "TEST_DATABASE_URL absent : test qui demande une vraie base PostgreSQL"
        )
    return url


@pytest.fixture(autouse=True)
def fresh_settings():
    """Les réglages sont mis en cache : chaque test repart de l'environnement qu'il a posé."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def restore_logging():
    """setup_logging modifie les journaux globaux : on remet tout en place après chaque test."""
    names = ("", "uvicorn", "uvicorn.error", "uvicorn.access")
    saved = {
        n: (
            list(logging.getLogger(n).handlers),
            logging.getLogger(n).level,
            logging.getLogger(n).propagate,
        )
        for n in names
    }
    yield
    for n, (handlers, level, propagate) in saved.items():
        logger = logging.getLogger(n)
        logger.handlers[:] = handlers
        logger.setLevel(level)
        logger.propagate = propagate


@pytest_asyncio.fixture
async def clean_token(db_url):
    result = alembic("upgrade", "head", database_url=db_url)
    assert result.returncode == 0, result.stderr
    eng = make_engine(db_url)
    async with eng.begin() as conn:
        await conn.execute(text("DELETE FROM provider_token"))
    await eng.dispose()


@pytest.fixture
def on_fake(monkeypatch):
    """Fait pointer `open_feed` des commandes vers le faux serveur."""

    def install(fake: FakeCTrader, clock=None):
        url = fake.url

        def open_feed(settings, engine):
            async def authorize(client, account_id):
                await ctoken.authorize_account(engine, client, account_id)

            kwargs = {} if clock is None else {"clock": clock}
            return CTraderFeed(
                CTraderClient(url, "app-id", "app-secret", bars_per_second=1000),
                settings.ctrader_account_id,
                settings.ctrader_symbol,
                authorize,
                **kwargs,
            )

        monkeypatch.setattr(cli, "open_feed", open_feed)

    return install
