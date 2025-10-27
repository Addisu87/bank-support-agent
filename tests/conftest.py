import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.models.base import Base
from app.main import app
from app.db.session import get_db
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    # Ensure we have a valid database URL
    test_db_url = settings.current_database_url
    engine = create_async_engine(test_db_url, echo=False, future=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create a fresh database session for each test"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture
def client(test_session):
    """Create test client with overridden dependencies"""
    def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db  
    yield TestClient(app)
    app.dependency_overrides.clear()
