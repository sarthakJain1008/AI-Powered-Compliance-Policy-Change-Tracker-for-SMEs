"""Alembic environment configuration for async SQLAlchemy.

This file is executed by Alembic when running ``alembic upgrade``,
``alembic revision --autogenerate``, etc.  It wires up:

* The async engine sourced from the application's settings.
* The ``Base.metadata`` so autogenerate can compare the ORM models against
  the live database schema and produce accurate migration scripts.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Import app objects — must happen before any Alembic internals reference them
# ---------------------------------------------------------------------------

# Load settings so DATABASE_URL is available
from app.core.config import settings  # noqa: E402

# Import Base and all models so metadata is fully populated
from app.db.base import Base  # noqa: E402
import app.models.user  # noqa: F401, E402  — registers User table on Base.metadata

# ---------------------------------------------------------------------------
# Alembic Config object (wraps alembic.ini)
# ---------------------------------------------------------------------------

config = context.config

# Override the sqlalchemy.url from alembic.ini with the value from settings so
# there is a single source of truth.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata drives autogenerate comparison
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration (no live DB connection)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This emits SQL to stdout/file without connecting to a database — useful
    for reviewing or applying migrations manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration (async)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations synchronously within an already-open connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,         # Detect column-type changes in autogenerate
        compare_server_default=True,  # Detect server-default changes too
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a sync wrapper."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Disposable pool — Alembic runs once and exits
    )

    async with connectable.connect() as connection:
        # Alembic's context.run_migrations() is synchronous, so we bridge via
        # run_sync which executes the callable in the event loop's thread.
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry-point for online (connected) migrations."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
