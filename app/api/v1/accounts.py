from fastapi import APIRouter, Depends, HTTPException, status
from app.core.deps import get_current_user
from app.db.models import User
from app.services.account_service import get_accounts_by_user, create_account
from app.services.card_service import get_cards_by_user
from app.services.transaction_service import get_transactions
from app.services.card_service import block_card_by_number
from app.models.account import CreateAccountRequest, AccountCreationResponse, Account
from app.models.transaction import TransactionInfo
from app.models.card import CardInfo, CardBlockResponse

router = APIRouter()

@router.post("/accounts", response_model=AccountCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_account_endpoint(request: CreateAccountRequest, current_user: User = Depends(get_current_user)):
    """
    Create a new bank account for a user.
    """
    try:
        account = await create_account(
            user_id=current_user.id,
            bank_id=request.bank_id,
            account_type=request.account_type,
            balance=request.balance,
            currency=request.currency
        )
            
        return AccountCreationResponse(
            status="success",
            message="Account created successfully",
            account_number=account.account_number,
            account_type=account.account_type,
            balance=account.balance,
            currency=account.currency,
            created_at=account.created_at
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")

@router.get("/accounts", response_model=list[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    """Get all accounts for the current user."""
    accounts = await get_accounts_by_user(current_user.id)
    if not accounts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No accounts found for this user")
    return accounts

@router.get("/accounts/{account_number}/transactions", response_model=list[TransactionInfo])
async def get_transactions_for_account(account_number: str, current_user: User = Depends(get_current_user)):
    """Get all transactions for a specific account."""
    # We need to get the account id from the account number
    accounts = await get_accounts_by_user(current_user.id)
    account = next((acc for acc in accounts if acc.account_number == account_number), None)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    transactions = await get_transactions(account.id)
    if not transactions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No transactions found for this account")
    return transactions

@router.get("/cards", response_model=list[CardInfo])
async def get_cards(current_user: User = Depends(get_current_user)):
    """Get all cards for the current user."""
    cards = await get_cards_by_user(current_user.id)
    if not cards:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cards found for this user")
    return cards

@router.post("/cards/{card_number}/block", response_model=CardBlockResponse)
async def block_card(card_number: str, current_user: User = Depends(get_current_user)):
    """
    Block a card.
    """
    result = await block_card_by_number(card_number, current_user.id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found or permission denied.")
    
    card = result["card"]
    if result.get("already_blocked"):
        return CardBlockResponse(
            status="success",
            message="Card is already blocked.",
            card_number=card.card_number,
            card_type=card.card_type,
            card_status=card.status
        )
    else:
        return CardBlockResponse(
            status="success",
            message="Card blocked successfully.",
            card_number=card.card_number,
            card_type=card.card_type,
            card_status=card.status
        )