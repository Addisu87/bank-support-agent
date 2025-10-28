from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.models.base import Base

# database connection
database_url = settings.current_database_url

# Create async engine
engine = create_async_engine(
    database_url, echo=True, future=True, poolclass=NullPool
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Database initialization
async def create_tables():
    """Create all tables (for testing/development)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
