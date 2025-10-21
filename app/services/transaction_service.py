import uuid

import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.account import Account
from app.db.models.transaction import Transaction, TransactionStatus, TransactionType
from app.schemas.transaction import (
    DepositRequest,
    TransactionCreate,
    TransactionQuery,
    TransferRequest,
    WithdrawRequest,
)
from app.services.account_service import (
    get_account_by_id,
    get_account_by_number,
    update_account_balance_internal,
)

# ------------------------
# 🔧 Utility Functions
# ------------------------


async def generate_transaction_reference() -> str:
    """Generate unique transaction reference"""
    return f"TXN{uuid.uuid4().hex[:12].upper()}"


# ------------------------
# 💰 Transaction CRUD Functions
# ------------------------


async def create_transaction(
    db: AsyncSession,
    transaction_data: TransactionCreate,
    status: TransactionStatus = TransactionStatus.COMPLETED,
) -> Transaction:
    with logfire.span(
        "create_transaction",
        account_id=transaction_data.account_id,
        amount=transaction_data.amount,
    ):
        # Verify account exists
        account = await db.get(Account, transaction_data.account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        transaction = Transaction(
            **transaction_data.model_dump(),
            reference=transaction_data.reference
            or await generate_transaction_reference(),
            status=status,
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return transaction


async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Transaction:
    with logfire.span("get_transaction_by_id", transaction_id=transaction_id):
        """Get transaction by ID"""
        return await db.get(Transaction, transaction_id)


async def get_transaction_by_reference(db: AsyncSession, reference: str) -> Transaction:
    """Get transaction by reference number"""
    with logfire.span("get_transaction_by_reference", reference=reference):
        result = await db.execute(
            select(Transaction)
            .filter(Transaction.reference == reference)
            .order_by(Transaction.created_at.desc())
        )
        return result.scalar_one_or_none()


async def get_account_transactions(
    db: AsyncSession, query: TransactionQuery
) -> list[Transaction]:
    with logfire.span("get_account_transactions", query=query.model_dump()):
        stmt = select(Transaction)

        if query.account_id:
            stmt = stmt.filter(Transaction.account_id == query.account_id)

        if query.transaction_type:
            stmt = stmt.filter(Transaction.transaction_type == query.transaction_type)

        if query.start_date:
            stmt = stmt.filter(Transaction.created_at >= query.start_date)

        if query.end_date:
            stmt = stmt.filter(Transaction.created_at <= query.end_date)

        stmt = stmt.offset(query.offset).limit(query.limit)
        stmt = stmt.order_by(Transaction.created_at.desc())

        result = await db.execute(stmt)
        return result.scalars().all()


async def get_transaction_summary(db: AsyncSession, account_id: int) -> dict:
    with logfire.span("get_transaction_summary", account_id=account_id):
        """Get transaction summary for an account"""
        deposit_stmt = select(Transaction.transaction_type, Transaction.amount).filter(
            Transaction.account_id == account_id
        )
        result = await db.execute(deposit_stmt)
        transactions = result.fetchall()

        summary = {
            "total_deposits": 0,
            "total_withdrawals": 0,
            "total_transfers": 0,
            "total_payments": 0,
        }

        for tx_type, amount in transactions:
            if tx_type == TransactionType.DEPOSIT:
                summary["total_deposits"] += amount
            elif tx_type == TransactionType.WITHDRAWAL:
                summary["total_withdrawals"] += amount
            elif tx_type == TransactionType.TRANSFER:
                summary["total_transfers"] += amount
            elif tx_type == TransactionType.PAYMENT:
                summary["total_payments"] += amount

        summary["net_flow"] = (
            summary["total_deposits"]
            - summary["total_withdrawals"]
            - summary["total_transfers"]
            - summary["total_payments"]
        )

        return summary


async def get_recent_transactions(
    db: AsyncSession, user_id: int, limit: int = 10
) -> list[Transaction]:
    """Get recent transactions for a user across all accounts"""
    with logfire.span("get_recent_transactions", user_id=user_id, limit=limit):
        result = await db.execute(
            select(Transaction)
            .join(Account)
            .filter(Account.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def delete_transaction(db: AsyncSession, transaction_id: int) -> bool:
    """Delete transaction by ID"""
    with logfire.span("delete_transaction", transaction_id=transaction_id):
        transaction = await get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        await db.delete(transaction)
        await db.commit()
        return True


# ------------------------
# 💰 Business Operations
# ------------------------


async def deposit_funds(
    db: AsyncSession, deposit_data: DepositRequest, user_id: int
) -> Transaction:
    """Deposit funds into account"""
    account = await get_account_by_number(db, deposit_data.account_number)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    # Check if user owns the account (if user_id is provided)
    if user_id and account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deposit to this account",
        )

    # Update account balance
    account.balance += deposit_data.amount
    account.available_balance += deposit_data.amount

    # Create transaction record
    transaction_data = TransactionCreate(
        account_id=account.id,
        amount=deposit_data.amount,
        transaction_type=TransactionType.DEPOSIT,
        description=deposit_data.description,
    )

    transaction = await create_transaction(db, transaction_data)
    await db.commit()
    return transaction


async def withdraw_funds(
    db: AsyncSession, withdraw_data: WithdrawRequest, user_id: int
) -> Transaction:
    """Withdraw funds from account"""
    account = await get_account_by_number(db, withdraw_data.account_number)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    # Check if user owns the account (if user_id is provided)
    if user_id and account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to withdraw from this account",
        )

    # Check sufficient funds
    if account.available_balance < withdraw_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
        )

    # Update account balance
    account.balance -= withdraw_data.amount
    account.available_balance -= withdraw_data.amount

    # Create transaction record
    transaction_data = TransactionCreate(
        account_id=account.id,
        amount=-withdraw_data.amount,  # Negative amount for withdrawal
        transaction_type=TransactionType.WITHDRAWAL,
        description=withdraw_data.description,
    )

    transaction = await create_transaction(db, transaction_data)
    await db.commit()
    return transaction


async def transfer_funds(
    db: AsyncSession, transfer_data: TransferRequest, user_id: int
) -> dict:
    """Transfer funds between accounts"""
    from_account = await get_account_by_number(db, transfer_data.from_account_number)
    to_account = await get_account_by_number(db, transfer_data.to_account_number)

    if not from_account or not to_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both accounts not found",
        )

    # Check if user owns the from_account (if user_id is provided)
    if user_id and from_account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to transfer from this account",
        )

    if from_account.balance < transfer_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
        )

    # Update balances
    await update_account_balance_internal(db, from_account.id, -transfer_data.amount)
    await update_account_balance_internal(db, to_account.id, transfer_data.amount)

    # Create transaction records for both accounts
    reference = await generate_transaction_reference()

    # Outgoing transaction
    outgoing_tx_data = TransactionCreate(
        account_id=from_account.id,
        amount=-transfer_data.amount,
        transaction_type=TransactionType.TRANSFER,
        description=f"Transfer to {to_account.account_number} - {transfer_data.description}",
        reference=reference,
    )

    # Incoming transaction
    incoming_tx_data = TransactionCreate(
        account_id=to_account.id,
        amount=transfer_data.amount,
        transaction_type=TransactionType.TRANSFER,
        description=f"Transfer from {from_account.account_number} - {transfer_data.description}",
        reference=reference,
    )

    # Create transactions without storing the returned objects
    await create_transaction(db, outgoing_tx_data)
    await create_transaction(db, incoming_tx_data)

    await db.commit()

    return {
        "message": "Transfer completed successfully",
        "reference": reference,
        "from_account": from_account.account_number,
        "to_account": to_account.account_number,
        "amount": transfer_data.amount,
        "new_balance": from_account.balance,
    }


async def create_interbank_transfer(
    db: AsyncSession,
    from_account_id: int,
    to_account_number: str,
    amount: float,
    description: str,
) -> dict:
    """Create inter-bank transfer (simplified implementation)"""
    from_account = await get_account_by_id(db, from_account_id)
    if not from_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found"
        )

    # Update source account balance
    from_account.balance -= amount
    from_account.available_balance -= amount

    # Create transaction record
    transaction_data = TransactionCreate(
        account_id=from_account.id,
        amount=-amount,
        transaction_type=TransactionType.TRANSFER,
        description=f"Inter-bank transfer to {to_account_number}"
        + (f" - {description}" if description else ""),
    )

    transaction = await create_transaction(
        db,
        transaction_data,
        status=TransactionStatus.PENDING,  # Inter-bank transfers might be pending
    )

    await db.commit()

    return {
        "message": "Inter-bank transfer initiated",
        "reference": transaction.reference,
        "amount": amount,
        "from_account": from_account.account_number,
        "to_account": to_account_number,
        "fee": 0.0,
        "status": "pending",
    }
