from app.db.models import Transaction, Account
from app.db.postgres import AsyncSessionLocal
from sqlalchemy import select

async def create_transaction(account_id: int, amount: float, currency: str, transaction_type: str = "payment", description: str = "", merchant: str = None):
    async with AsyncSessionLocal() as session: 
        tx = Transaction(account_id=account_id, amount=amount, currency=currency, transaction_type=transaction_type, description=description, merchant=merchant)
        session.add(tx)
        # update account balance
        acct = await session.get(Account, account_id)
        if acct: 
            acct.balance = (acct.balance or 0.0) + amount
            session.add(acct)
        await session.commit()
        await session.refresh(tx)
        return tx

async def get_transactions(account_id: int, limit: int = 10):
    async with AsyncSessionLocal() as session: 
        result = await session.execute(select(Transaction).filter_by(account_id=account_id).order_by(Transaction.timestamp.desc()).limit(limit))
        return result.scalars().all()