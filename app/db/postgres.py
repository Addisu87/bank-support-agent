# SQLAlchemy engine, sessionmaker, async DB access
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import(Base)

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Async engine
engine= create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,  class_=AsyncSession, expire_on_commit=False
)

# Dependency to get DB session
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session: 
        yield session     

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        