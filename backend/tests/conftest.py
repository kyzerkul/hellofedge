"""Outils partagés des tests.

Les tests qui ont besoin d'une vraie base PostgreSQL lisent TEST_DATABASE_URL
(une base jetable, jamais celle de production). Sans elle, ils sont sautés.
"""

import logging
import os

import pytest

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
