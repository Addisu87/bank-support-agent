from app.db.models import Bank
from app.db.postgres import AsyncSessionLocal
from sqlalchemy import select

async def create_bank(name: str, bic: str = None, country: str = None):
    async with AsyncSessionLocal() as session: 
        bank = Bank(name=name, bic=bic, country=country)
        session.add(bank)
        await session.commit()
        await session.refresh(bank)
        return bank

async def list_banks():
    """Retrieve a list of all banks."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Bank))
        return result.scalars().all()