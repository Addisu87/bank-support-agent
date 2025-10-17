from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
import random

from app.db.schema import User, Account, Transaction, Card
from app.core.deps import get_current_active_user
from app.db.session import get_session
from app.models.account import CreateAccountRequest, AccountCreationResponse, AccountInfo
from app.models.transaction import TransactionInfo
from app.models.card import CardInfo, CardBlockResponse

router = APIRouter()


@router.post("/create-account", response_model=AccountCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: CreateAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Create a new bank account for the current user."""
    try:
        account_number = getattr(request, "account_number", None) or f"ACCT{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}{random.randint(1000, 9999)}"
        new_account = Account(
            user_id=current_user.id,
            bank_id=request.bank_id,
            account_number=account_number,
            balance=request.balance or 0.0,
            currency=request.currency or "USD",
            account_type=request.account_type or "checking"
        )
        db.add(new_account)
        await db.commit()
        await db.refresh(new_account)

        return AccountCreationResponse(
            status="success",
            message="Account created successfully",
            account_number=new_account.account_number,
            account_type=new_account.account_type,
            balance=new_account.balance,
            currency=new_account.currency,
            created_at=new_account.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")


@router.get("/", response_model=list[AccountInfo])
async def get_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Get all accounts for the current user."""
    result = await db.execute(select(Account).filter_by(user_id=current_user.id))
    accounts = result.scalars().all()
    if not accounts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No accounts found for this user")
    return accounts


@router.get("/{user_id}/accounts", response_model=list[AccountInfo])
async def get_user_accounts(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Get accounts for a specific user (self only for now)."""
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user's accounts")
    
    result = await db.execute(select(Account).filter_by(user_id=user_id))
    accounts = result.scalars().all()
    if not accounts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No accounts found for this user")
    return accounts


@router.get("/{account_number}/transactions", response_model=list[TransactionInfo])
async def get_transactions_for_account(
    account_number: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Get all transactions for a specific account."""
    # Direct query to find the account
    result = await db.execute(select(Account).filter_by(user_id=current_user.id, account_number=account_number))
    account = result.scalars().first()
    
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    # Direct query to fetch transactions
    tx_result = await db.execute(select(Transaction).filter_by(account_id=account.id))
    transactions = tx_result.scalars().all()
    
    if not transactions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No transactions found for this account")
    return transactions

@router.post("/cards", response_model=CardInfo, status_code=status.HTTP_201_CREATED)
async def create_card(
    account_id: int,
    card_number: str,
    card_type: str = "debit",
    expiry_date: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Create a new card for a specific account."""
    # Optional: verify account exists
    result = await db.execute(select(Account).filter_by(id=account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    new_card = Card(
        account_id=account_id,
        card_number=card_number,
        card_type=card_type,
        expiry_date=expiry_date
    )

    db.add(new_card)
    await db.commit()
    await db.refresh(new_card)

    return new_card 

@router.get("/cards", response_model=list[CardInfo])
async def get_cards(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Get all cards for the current user."""
    result = await db.execute(select(Card).filter_by(user_id=current_user.id))
    cards = result.scalars().all()
    if not cards:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cards found for this user")
    return cards

@router.get("/cards/{card_number}", response_model=CardInfo)
async def get_card(
    card_number: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Get a single card by number."""
    result = await db.execute(
        select(Card).join(Account).filter(
            Card.card_number == card_number,
            Account.user_id == current_user.id
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.post("/cards/{card_number}/block", response_model=CardBlockResponse)
async def block_card(
    card_number: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Block a card."""
    result = await db.execute(select(Card).filter_by(user_id=current_user.id, card_number=card_number))
    card = result.scalars().first()
    
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found or permission denied.")
    
    if card.status == "blocked":
        return CardBlockResponse(
            status="success",
            message="Card is already blocked.",
            card_number=card.card_number,
            card_type=card.card_type,
            card_status=card.status
        )

    # Block the card
    card.status = "blocked"
    db.add(card)
    await db.commit()
    await db.refresh(card)

    return CardBlockResponse(
        status="success",
        message="Card blocked successfully.",
        card_number=card.card_number,
        card_type=card.card_type,
        card_status=card.status
    )
