import uuid

import logfire
from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.account import Account
from app.db.models.transaction import Transaction, TransactionStatus, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionQuery
from app.services.account_service import (
    get_account_by_id,
    get_account_by_number,
    update_account_balance,
)
from app.services.card_service import get_card_by_number, validate_card_transaction

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
    db: AsyncSession, transaction_data: TransactionCreate
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
            account_id=transaction_data.account_id,
            amount=transaction_data.amount,
            transaction_type=transaction_data.transaction_type,
            description=transaction_data.description,
            reference=transaction_data.reference
            or await generate_transaction_reference(),
            status=TransactionStatus.COMPLETED,
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return transaction


async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Transaction:
    with logfire.span("get_transaction_by_id", transaction_id=transaction_id):
        return await db.get(Transaction, transaction_id)


async def get_transaction_by_reference(db: AsyncSession, reference: str) -> Transaction:
    """Get transaction by reference number"""
    with logfire.span("get_transaction_by_reference", reference=reference):
        result = await db.execute(
            select(Transaction).filter(Transaction.reference == reference)
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
        # Get total deposits
        deposit_stmt = select(Transaction.amount).filter(
            and_(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.DEPOSIT,
            )
        )
        result = await db.execute(deposit_stmt)
        total_deposits = sum(row[0] for row in result.fetchall() or [0])

        # Get total withdrawals
        withdrawal_stmt = select(Transaction.amount).filter(
            and_(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
            )
        )
        result = await db.execute(withdrawal_stmt)
        total_withdrawals = sum(row[0] for row in result.fetchall() or [0])

        # Get total transfers
        transfer_stmt = select(Transaction.amount).filter(
            and_(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.TRANSFER,
            )
        )
        result = await db.execute(transfer_stmt)
        total_transfers = sum(row[0] for row in result.fetchall() or [0])

        return {
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "total_transfers": total_transfers,
            "net_flow": total_deposits - total_withdrawals - total_transfers,
        }


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
# 💳 Card Transaction Functions
# ------------------------


async def create_transaction_with_card(
    db: AsyncSession, transaction_data: TransactionCreate, card_number: str
) -> Transaction:
    with logfire.span(
        "create_transaction_with_card",
        card_number=card_number[-4:],
        amount=transaction_data.amount,
    ):
        # Verify card and account
        if not await validate_card_transaction(
            db, card_number, transaction_data.amount
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card transaction not authorized",
            )

        card = await get_card_by_number(db, card_number)
        transaction_data.card_id = card.id

        return await create_transaction(db, transaction_data)


async def get_card_transactions(
    db: AsyncSession, card_id: int, limit: int = 50, offset: int = 0
) -> list[Transaction]:
    with logfire.span("get_card_transactions", card_id=card_id):
        stmt = (
            select(Transaction)
            .filter(Transaction.card_id == card_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()


# ------------------------
# 🏦 Transfer Functions
# ------------------------


async def create_interbank_transfer(
    db: AsyncSession,
    from_account_id: int,
    to_account_number: str,
    amount: float,
    description: str = None,
) -> dict:
    """Create inter-bank transfer"""
    with logfire.span(
        "interbank_transfer", from_account_id=from_account_id, amount=amount
    ):
        # Get source account
        from_account = await get_account_by_id(db, from_account_id)
        if not from_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found"
            )

        # Check if target account is in same bank
        to_account = await get_account_by_number(db, to_account_number)
        if to_account and to_account.bank_id == from_account.bank_id:
            # Same bank transfer
            return await create_same_bank_transfer(
                db, from_account_id, to_account.id, amount, description
            )
        else:
            # Inter-bank transfer
            return await create_interbank_transfer_processing(
                db, from_account, to_account_number, amount, description
            )


async def create_same_bank_transfer(
    db: AsyncSession,
    from_account_id: int,
    to_account_id: int,
    amount: float,
    description: str = None,
) -> dict:
    """Create same bank transfer"""
    with logfire.span(
        "same_bank_transfer",
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
    ):
        # Update balances
        from_account = await update_account_balance(db, from_account_id, -amount)
        to_account = await update_account_balance(db, to_account_id, amount)

        # Create transaction records
        transfer_desc = f"Transfer to account {to_account.account_number}" + (
            f" - {description}" if description else ""
        )

        outgoing_tx = Transaction(
            account_id=from_account_id,
            amount=-amount,
            transaction_type=TransactionType.TRANSFER,
            description=transfer_desc,
            reference=await generate_transaction_reference(),
            status=TransactionStatus.COMPLETED,
        )

        incoming_tx = Transaction(
            account_id=to_account_id,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            description=f"Transfer from account {from_account.account_number}",
            reference=outgoing_tx.reference,  # Same reference for both sides
            status=TransactionStatus.COMPLETED,
        )

        db.add_all([outgoing_tx, incoming_tx])
        await db.commit()

        return {
            "message": "Transfer completed successfully",
            "reference": outgoing_tx.reference,
            "from_account": from_account.account_number,
            "to_account": to_account.account_number,
            "amount": amount,
            "new_balance": from_account.balance,
        }


async def create_interbank_transfer_processing(
    db: AsyncSession,
    from_account: Account,
    to_account_number: str,
    amount: float,
    description: str,
) -> dict:
    """Process inter-bank transfer (simplified implementation)"""
    with logfire.span(
        "interbank_transfer_processing",
        from_account=from_account.account_number,
        amount=amount,
    ):
        # Update source account balance
        from_account = await update_account_balance(db, from_account.id, -amount)

        # Create transaction record
        transaction = Transaction(
            account_id=from_account.id,
            amount=-amount,
            transaction_type=TransactionType.TRANSFER,
            description=f"Inter-bank transfer to {to_account_number}"
            + (f" - {description}" if description else ""),
            reference=f"IBT{uuid.uuid4().hex[:12].upper()}",
            status=TransactionStatus.PENDING,  # Inter-bank transfers might be pending
            metadata={
                "type": "interbank",
                "to_account": to_account_number,
                "from_bank": from_account.bank.name if from_account.bank else "Unknown",
                "processing_fee": 0.0,
            },
        )

        db.add(transaction)
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
