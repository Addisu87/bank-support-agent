from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    DepositRequest,
    TransactionQuery,
    TransactionResponse,
    TransferRequest,
    WithdrawalRequest,
)
from app.services.account_service import get_account_by_id
from app.services.transaction_service import (
    create_transaction,
    get_transaction,
    get_transactions,
    get_user_all_transactions,
    get_transaction_summary,
    create_interbank_transfer,
    transfer_funds,
    deposit_funds,
    withdraw_funds,
    _verify_transaction_ownership,
)

router = APIRouter(tags=["transactions"])

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new transaction for current user"""
    # Verify account belongs to user
    account = await get_account_by_id(db, transaction_data.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Account not found or not authorized"
        )
    
    transaction = await create_transaction(db, transaction_data)
    return transaction

@router.get("/", response_model=List[TransactionResponse])
async def get_all_transactions(
    account_id: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get transactions with filtering"""
    if account_id:
        # Verify account belongs to user if specified
        account = await get_account_by_id(db, account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )
        query = TransactionQuery(account_id=account_id, limit=limit)
        transactions = await get_transactions(db, query)
    else:
        # Use the renamed function for user transactions
        transactions = await get_user_all_transactions(db, current_user.id, limit)
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_by_id(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific transaction details"""
    transaction = await get_transaction(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Verify transaction belongs to user using helper
    await _verify_transaction_ownership(db, transaction, current_user.id)
    return transaction

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

@router.delete("/{transaction_id}")
async def delete_transaction_by_id(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a transaction"""
    success = await delete_transaction(db, transaction_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    
    return {"message": "Transaction deleted successfully"}

@router.post("/interbank-transfer", status_code=status.HTTP_200_OK)
async def interbank_transfer(
    from_account_id: int,
    to_account_number: str,
    amount: float,
    description: str | None = None,
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
    withdraw_data: WithdrawalRequest,
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
