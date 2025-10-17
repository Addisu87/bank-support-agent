from app.db.schema import Transaction, Account
from sqlalchemy import select
from app.db.session import AsyncSession
from app.db.session import get_session
from fastapi import Depends

async def create_transaction(account_id: int, amount: float, currency: str, transaction_type: str = "payment", description: str = "", merchant: str | None = None, balance: float | None = None, 
    db: AsyncSession = Depends(get_session)):
    tx = Transaction(account_id=account_id, amount=amount, currency=currency, transaction_type=transaction_type, description=description, merchant=merchant)
    db.add(tx)
    # update account balance
    acct = await db.get(Account, account_id)
    if acct: 
        acct.balance = (acct.balance or 0.0) + amount
        db.add(acct)
    await db.commit()
    await db.refresh(tx)
    return tx

async def get_transactions(
    account_id: int,
    limit: int = 10,  
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(Transaction).filter_by(account_id=account_id).order_by(Transaction.timestamp.desc()).limit(limit))
    return result.scalars().all()