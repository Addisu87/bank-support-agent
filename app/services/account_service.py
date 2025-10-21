import uuid

import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.account import Account, AccountStatus
from app.db.models.bank import Bank
from app.db.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate


async def generate_account_number() -> str:
    """Generate unique account number"""
    return f"ACC{uuid.uuid4().hex[:12].upper()}"


async def create_account(
    db: AsyncSession, user_id: int, account_data: AccountCreate
) -> Account:
    """Create a new account with bank relationship"""
    with logfire.span("create_account", user_id=user_id):
        # Verify user exists
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify bank exists
        bank = await db.get(Bank, account_data.bank_id)
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found"
            )

        account_number = await generate_account_number()
        account = Account(
            **account_data.model_dump(),
            user_id=user_id,
            account_number=account_number,
            balance=0.0,
            available_balance=0.0,
            status=AccountStatus.ACTIVE,
        )

        db.add(account)
        await db.commit()
        await db.refresh(account)

        # IMPORTANT: Use the same session to reload with relationships
        result = await db.execute(
            select(Account)
            .options(selectinload(Account.bank))
            .where(Account.id == account.id)
        )
        account_with_bank = result.scalar_one()
        return account_with_bank


async def get_all_accounts(db: AsyncSession, user_id: int) -> list[Account]:
    """Get all accounts for a specific user"""
    with logfire.span("get_all_accounts", user_id=user_id):
        result = await db.execute(
            select(Account)
            .options(selectinload(Account.bank))
            .where(Account.user_id == user_id)
            .order_by(Account.created_at.desc())
        )

        return result.scalars().all()


async def get_account_by_id(db: AsyncSession, account_id: int) -> Account | None:
    """Get account by ID with bank relationship"""
    with logfire.span("get_account_by_id", account_id=account_id):
        result = await db.execute(
            select(Account)
            .options(selectinload(Account.bank))
            .where(Account.id == account_id)
        )
        return result.scalar_one_or_none()


async def get_account_by_number(
    db: AsyncSession, account_number: str
) -> Account | None:
    with logfire.span("get_account_by_number", account_number=account_number):
        result = await db.execute(
            select(Account)
            .options(selectinload(Account.bank))
            .where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none()


async def update_account_balance(
    db: AsyncSession, account_id: int, amount: float
) -> Account:
    """Update account balance (for internal use in transactions)"""
    with logfire.span("update_account_balance", account_id=account_id, amount=amount):
        # Get account WITH bank relationship loaded
        result = await db.execute(
            select(Account)
            .options(selectinload(Account.bank))
            .where(Account.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        # Update balance
        account.balance += amount
        account.available_balance += amount

        await db.commit()
        await db.refresh(account)
        return account


async def update_account(
    db: AsyncSession, account_id: int, account_data: AccountUpdate, user_id: int = None
) -> Account:
    """Update account details (for user-initiated updates)"""
    with logfire.span(
        "update_account_details",
        account_id=account_id,
        update_data=account_data.model_dump(),
    ):
        # Get account WITH bank relationship loaded
        result = await db.execute(
            select(Account)
            .options(selectinload(Account.bank))
            .where(Account.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        # Check if user owns the account (if user_id is provided)
        if user_id and account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this account",
            )

        # Update fields (exclude balance fields from user updates)
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(account, field) and value is not None:
                setattr(account, field, value)

        await db.commit()
        await db.refresh(account)
        return account


async def delete_account(
    db: AsyncSession, account_id: int, user_id: int = None
) -> bool:
    """Delete account by ID"""
    with logfire.span("delete_account", account_id=account_id):
        account = await get_account_by_id(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        # Check if user owns the account (if user_id is provided)
        if user_id and account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this account",
            )

        if account.balance > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete account with positive balance",
            )

        await db.delete(account)
        await db.commit()
        return True
