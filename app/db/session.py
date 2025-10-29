from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.models.base import Base

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True, 
    pool_pre_ping=True,     # detect dead/stale connections
    pool_size=5,            # small pool
    max_overflow=10,        # allow temporary spikes
)

# Use async_sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Dependency for FastAPI - Let FastAPI handle transactions
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Database initialization
async def create_tables():
    """Create all tables (for testing/development)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)