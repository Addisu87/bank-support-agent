from sqlalchemy import select
from app.db.models import Account, User
from app.db.postgres import AsyncSessionLocal
import datetime
import random
from app.services.user_service import get_user_by_email

async def get_user_id_from_email(email: str) -> int | None:
    user = await get_user_by_email(email)
    return user.id if user else None

async def get_account_id_for_user(user_id: int, account_number: str) -> int | None:
    accounts = await get_accounts_by_user(user_id)
    for account in accounts:
        if account.account_number == account_number:
            return account.id
    return None

async def create_account(user_id: int, bank_id: int, account_number: str | None = None, balance: float | None = None, currency: str | None = None, account_type: str | None = None):
    async with AsyncSessionLocal() as session: 
        if account_number is None: 
            account_number = f"ACCT{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}{random.randint(1000, 9999)}"
        account = Account(user_id=user_id, bank_id=bank_id, account_number=account_number, balance=balance, currency=currency, account_type=account_type)
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

async def get_accounts_by_user(user_id: int):
    async with AsyncSessionLocal() as session: 
        result = await session.execute(select(Account).filter_by(user_id=user_id))
        return result.scalars().all()