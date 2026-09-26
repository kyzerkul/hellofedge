"""Migrations Alembic. L'URL de la base vient de DATABASE_URL, jamais du fichier .ini.

Lancées par une étape dédiée du déploiement (`alembic upgrade head`), jamais au
démarrage du worker ou de l'api.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

from hellofedge.config import get_settings
from hellofedge.db import Base, async_url, make_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Les modèles s'enregistrent sur Base.metadata quand ils sont importés.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Écrit le SQL sans se connecter (`alembic upgrade head --sql`)."""
    context.configure(
        url=async_url(get_settings().database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = make_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
