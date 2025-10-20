import uuid

import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.db.models.account import Account
from app.db.models.user import User
from app.schemas.account import AccountCreate, TransferRequest


async def generate_account_number() -> str:
    """Generate unique account number"""
    return f"ACC{uuid.uuid4().hex[:12].upper()}"


async def get_account_by_id(db: AsyncSession, account_id: int) -> Account:
    with logfire.span("get_account_by_id", account_id=account_id):
        cache_key = f"account:{account_id}"
        cached = await cache.get_json(cache_key)
        if cached:
            return Account(**cached)

        account = await db.get(Account, account_id)
        if account:
            await cache.set_json(cache_key, account.__dict__)
        return account


async def get_account_by_number(db: AsyncSession, account_number: str) -> Account:
    with logfire.span("get_account_by_number", account_number=account_number):
        cache_key = f"account:number:{account_number}"
        cached = await cache.get_json(cache_key)
        if cached:
            return Account(**cached)

        result = await db.execute(
            select(Account).filter(Account.account_number == account_number)
        )
        account = result.scalar_one_or_none()
        if account:
            await cache.set_json(cache_key, account.__dict__)
        return account


async def create_account(
    db: AsyncSession, user_id: int, account_data: AccountCreate
) -> Account:
    with logfire.span("create_account", user_id=user_id):
        # Verify user exists
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        account_number = await generate_account_number()
        account = Account(
            user_id=user_id,
            account_number=account_number,
            account_type=account_data.account_type,
            currency=account_data.currency,
        )

        db.add(account)
        await db.commit()
        await db.refresh(account)

        # Clear cache
        await cache.clear_pattern(f"user_accounts:{user_id}")

        return account


async def get_user_accounts(db: AsyncSession, user_id: int) -> list[Account]:
    with logfire.span("get_user_accounts", user_id=user_id):
        cache_key = f"user_accounts:{user_id}"
        cached = await cache.get_json(cache_key)
        if cached:
            return [Account(**acc_data) for acc_data in cached]

        result = await db.execute(select(Account).filter(Account.user_id == user_id))
        accounts = result.scalars().all()
        await cache.set_json(cache_key, [acc.__dict__ for acc in accounts])
        return accounts


async def update_account_balance(
    db: AsyncSession, account_id: int, amount: float
) -> Account:
    with logfire.span("update_balance", account_id=account_id, amount=amount):
        account = await get_account_by_id(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        new_balance = account.balance + amount
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
            )

        account.balance = new_balance
        await db.commit()
        await db.refresh(account)

        # Clear cache
        await cache.delete(f"account:{account_id}")
        await cache.delete(f"account:number:{account.account_number}")
        await cache.clear_pattern(f"user_accounts:{account.user_id}")

        return account


async def transfer_funds(db: AsyncSession, transfer_data: TransferRequest) -> dict:
    with logfire.span("transfer_funds", transfer_data=transfer_data.model_dump()):
        from_account = await get_account_by_number(
            db, transfer_data.from_account_number
        )
        to_account = await get_account_by_number(db, transfer_data.to_account_number)

        if not from_account or not to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both accounts not found",
            )

        if from_account.balance < transfer_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
            )

        # Update balances
        from_account.balance -= transfer_data.amount
        to_account.balance += transfer_data.amount

        await db.commit()

        # Clear cache
        await cache.delete(f"account:{from_account.id}")
        await cache.delete(f"account:{to_account.id}")
        await cache.delete(f"account:number:{from_account.account_number}")
        await cache.delete(f"account:number:{to_account.account_number}")
        await cache.clear_pattern(f"user_accounts:{from_account.user_id}")
        await cache.clear_pattern(f"user_accounts:{to_account.user_id}")

        return {
            "from_account": from_account.account_number,
            "to_account": to_account.account_number,
            "amount": transfer_data.amount,
            "new_balance": from_account.balance,
        }


async def delete_account(db: AsyncSession, account_id: int) -> bool:
    """Delete account by ID"""
    with logfire.span("delete_account", account_id=account_id):
        account = await get_account_by_id(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        await db.delete(account)
        await db.commit()

        # Clear cache
        await cache.delete(f"account:{account_id}")
        await cache.delete(f"account:number:{account.account_number}")
        await cache.clear_pattern(f"user_accounts:{account.user_id}")

        return True


async def update_account_status(
    db: AsyncSession, account_id: int, status: str
) -> Account:
    """Update account status"""
    with logfire.span("update_account_status", account_id=account_id, status=status):
        account = await get_account_by_id(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        account.status = status
        await db.commit()
        await db.refresh(account)

        # Clear cache
        await cache.delete(f"account:{account_id}")
        await cache.delete(f"account:number:{account.account_number}")
        await cache.clear_pattern(f"user_accounts:{account.user_id}")

        return account
