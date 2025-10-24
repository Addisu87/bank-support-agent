import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bank import Bank
from app.schemas.bank import BankCreate, BankUpdate


async def get_bank_by_id(db: AsyncSession, bank_id: int) -> Bank:
    with logfire.span("get_bank_by_id", bank_id=bank_id):
        bank = await db.get(Bank, bank_id)
        return bank


async def get_bank_by_code(db: AsyncSession, bank_code: str) -> Bank:
    with logfire.span("get_bank_by_code", bank_code=bank_code):
        result = await db.execute(select(Bank).filter(Bank.code == bank_code))
        bank = result.scalar_one_or_none()
        return bank


async def get_all_active_banks(db: AsyncSession) -> list[Bank]:
    with logfire.span("get_all_active_banks"):
        result = await db.execute(
            select(Bank).filter(Bank.is_active == True).order_by(Bank.name)
        )
        banks = result.scalars().all()
        return banks


async def get_banks_by_country(db: AsyncSession, country: str) -> list[Bank]:
    """Get banks by country"""
    with logfire.span("get_banks_by_country", country=country):
        result = await db.execute(
            select(Bank)
            .filter(Bank.country == country, Bank.is_active == True)
            .order_by(Bank.name)
        )
        banks = result.scalars().all()
        return banks


async def create_bank(db: AsyncSession, bank_data: BankCreate) -> Bank:
    with logfire.span("create_bank", bank_name=bank_data.name):
        # Check if bank code already exists
        existing_bank = await get_bank_by_code(db, bank_data.code)
        if existing_bank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bank code already exists",
            )

        bank = Bank(**bank_data.model_dump())
        db.add(bank)
        await db.commit()
        await db.refresh(bank)
        return bank


async def update_bank(db: AsyncSession, bank_id: int, bank_data: BankUpdate) -> Bank:
    with logfire.span("update_bank", bank_id=bank_id):
        bank = await get_bank_by_id(db, bank_id)
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found"
            )

        update_data = bank_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank, field, value)

        await db.commit()
        await db.refresh(bank)
        return bank


async def delete_bank(db: AsyncSession, bank_id: int) -> bool:
    """Delete bank by ID"""
    with logfire.span("delete_bank", bank_id=bank_id):
        bank = await get_bank_by_id(db, bank_id)
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found"
            )

        await db.delete(bank)
        await db.commit()
        return True
