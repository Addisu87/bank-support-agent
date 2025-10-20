from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_db, get_current_active_user
from app.schemas.account import (
    AccountResponse, AccountCreate, 
    TransferRequest, AccountBalance
)

from app.db.models.user import User
from app.services.account_service import get_user_accounts, create_account,get_account_by_number

router = APIRouter(tags=["accounts"])

@router.get("/", response_model=List[AccountResponse])
async def get_my_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all accounts for current user"""
    accounts = await get_user_accounts(db, current_user.id)
    return accounts

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_new_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new account for current user"""
    account = await create_account(db, current_user.id, account_data)
    return account

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific account details"""
    account = await get_user_accounts(db, account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account

@router.get("/{account_number}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get account balance"""
    account = await get_account_by_number(db, account_number)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return AccountBalance(
        account_number=account.account_number,
        balance=account.balance,
        currency=account.currency
    )

@router.post("/transfer", status_code=status.HTTP_200_OK)
async def transfer_funds(
    transfer_data: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Transfer funds between accounts"""
    # Verify source account belongs to user
    from_account = await get_account_by_number(db, transfer_data.from_account_number)
    
    if not from_account or from_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source account not found"
        )
    
    result = await transfer_funds(transfer_data)
    return {"message": "Transfer completed successfully", "details": result}