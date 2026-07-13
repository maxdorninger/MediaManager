"""Shared fixtures for the repository test-suite.

The tests run against an in-memory SQLite database driven by ``aiosqlite``, so
the suite needs no running PostgreSQL. Note that the indexer models are
deliberately not imported: they use a PostgreSQL-only ARRAY column.
"""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from media_manager.database import Base
from media_manager.notification import models as notification_models

# Importing the model modules is what registers their tables on
# ``Base.metadata``; binding them here keeps the imports from looking unused.
_MODEL_MODULES = (notification_models,)


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Mirrors the production sessionmaker, notably ``expire_on_commit=False``."""
    return async_sessionmaker(engine, expire_on_commit=False)
