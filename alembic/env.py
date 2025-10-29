import sys, os, asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from alembic.util.exc import CommandError

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.models.account import Account
from app.db.models.bank import Bank
from app.db.models.base import BaseModel
from app.db.models.card import Card
from app.db.models.transaction import Transaction
from app.db.models.user import User
from app.core.config import settings

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
models = [User, Account, Bank, Transaction, Card]
target_metadata = BaseModel.metadata


def get_db_url() -> str:
    url = settings.DATABASE_URL or config.get_main_option("sqlalchemy.url")
    if not url or not url.startswith("postgres"):
        raise CommandError(f"Invalid or missing DATABASE_URL: {url!r}")
    return url

def run_migrations_offline():
    context.configure(
        url=get_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(conn):
    context.configure(connection=conn, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    engine = create_async_engine(get_db_url(), poolclass=pool.NullPool)
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
