import asyncio
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.db.models.base import Base
from app.main import app
from app.core.config import settings
from app.db.session import get_db
from unittest.mock import patch, AsyncMock

# Force test environment
os.environ["ENV_STATE"] = "test"
os.environ["DEEPSEEK_API_KEY"] = "test-key"  # dummy key for tests

# ------------------------
# ENGINE (CREATED PER FUNCTION)
# ------------------------
@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_size=3,
        max_overflow=0,
        pool_pre_ping=True,
    )
    # Drop and create tables once per session
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


# ------------------------
# SESSION FACTORY (REUSED)
# ------------------------
@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# ------------------------
# PER-TEST DATABASE SESSION
# ------------------------
@pytest_asyncio.fixture
async def db(session_factory):
    """Provide a fresh session per test, rollback at the end."""
    async with session_factory() as session:
        yield session
        await session.rollback()  # rollback all changes after test


# ------------------------
# FASTAPI TEST CLIENT
# ------------------------
@pytest_asyncio.fixture
async def client(db):
    """AsyncClient using the per-test session."""

    async def override_get_db():
        yield db  # reuse the same session in all requests in a test

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()



@pytest.fixture(autouse=True)
def mock_deepseek_provider():
    with patch(
        "app.services.llm_agent.DeepSeekProvider",
        new_callable=AsyncMock
    ) as mock_provider:
        yield mock_provider
