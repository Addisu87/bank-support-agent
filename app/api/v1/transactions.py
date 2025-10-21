from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.schemas.transaction import (
    DepositRequest,
    TransactionQuery,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)
from app.services.account_service import get_account_by_id
from app.services.transaction_service import (
    create_interbank_transfer,
    deposit_funds,
    get_account_transactions,
    get_recent_transactions,
    get_transaction_by_id,
    get_transaction_summary,
    transfer_funds,
    withdraw_funds,
)

router = APIRouter(tags=["transactions"])


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    query: TransactionQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get transactions with filtering"""
    # Verify account belongs to user if specified
    if query.account_id:
        account = await get_account_by_id(db, query.account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

    transactions = await get_account_transactions(db, query)
    return transactions


@router.get("/recent", response_model=List[TransactionResponse])
async def get_recent_user_transactions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get recent transactions for current user across all accounts"""
    transactions = await get_recent_transactions(db, current_user.id, limit)
    return transactions


@router.get("/summary/{account_id}")
async def get_account_transaction_summary(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get transaction summary for an account"""
    # Verify account belongs to user
    account = await get_account_by_id(db, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    summary = await get_transaction_summary(db, account_id)
    return summary


@router.post("/interbank-transfer", status_code=status.HTTP_200_OK)
async def interbank_transfer(
    from_account_id: int,
    to_account_number: str,
    amount: float,
    description: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create inter-bank transfer"""
    # Verify source account belongs to user
    from_account = await get_account_by_id(db, from_account_id)

    if not from_account or from_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found"
        )

    # Check sufficient funds
    if from_account.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
        )

    # Perform inter-bank transfer
    result = await create_interbank_transfer(
        db, from_account_id, to_account_number, amount, description
    )
    return result


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific transaction details"""
    transaction = await get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Verify transaction belongs to user
    account = await get_account_by_id(db, transaction.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transaction",
        )

    return transaction


@router.post("/deposit", response_model=TransactionResponse)
async def deposit_to_account(
    deposit_data: DepositRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deposit funds to account"""
    transaction = await deposit_funds(db, deposit_data, current_user.id)
    return transaction


@router.post("/withdraw", response_model=TransactionResponse)
async def withdraw_from_account(
    withdraw_data: WithdrawRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Withdraw funds from account"""
    transaction = await withdraw_funds(db, withdraw_data, current_user.id)
    return transaction


@router.post("/transfer", status_code=status.HTTP_200_OK)
async def transfer_from_account(
    transfer_data: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transfer funds between accounts"""
    result = await transfer_funds(db, transfer_data, current_user.id)
    return {"message": "Transfer completed successfully", "details": result}
