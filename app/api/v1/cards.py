from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_db, get_current_active_user
from app.schemas.card import CardResponse, CardCreate, CardUpdate, CardSecurityUpdate
from app.db.models.user import User
from app.db.models.card import CardStatus
from app.services.account_service import get_account_by_id
from app.services.card_service import get_user_cards, create_card, block_card,get_card_by_id, unblock_card, update_card,update_card_daily_limit

    
router = APIRouter(tags=["cards"])

@router.get("/cards", response_model=List[CardResponse])
async def get_my_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all cards for current user"""
    cards = await get_user_cards(db, current_user.id)
    return cards

@router.post("/cards/{account_id}", response_model=CardResponse)
async def create_new_card(
    account_id: int,
    card_data: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new card for an account"""
    card = await create_card(db, account_id, card_data, current_user.id)
    return card

@router.post("/cards/{card_id}/block", response_model=CardResponse)
async def block_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Block a card"""
    card = await block_card(db, card_id, current_user.id)
    return card

@router.post("/cards/{card_id}/unblock", response_model=CardResponse)
async def unblock_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Unblock a card"""
    card = await unblock_card(db, card_id, current_user.id)
    return card

@router.put("/cards/{card_id}/limit")
async def update_card_limit(
    card_id: int,
    new_limit: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update card daily limit"""
    card = await update_card_daily_limit(db, card_id, new_limit, current_user.id)
    return card


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific card details"""
    card = await get_card_by_id(db, card_id)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Verify card belongs to user
    account = await get_account_by_id(db, card.account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this card"
        )
    
    # Mask card number for response
    card.card_number = f"****{card.card_number[-4:]}"
    
    return card


@router.get("/{card_id}/transactions")
async def get_card_transactions(
    card_id: int,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get transactions for a specific card"""
    # Verify card belongs to user
    card = await get_card_by_id(db, card_id)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    

    account = await get_account_by_id(db, card.account_id)
    
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this card's transactions"
        )
    
    transactions = await get_card_transactions(card_id, limit, offset)
    
    return transactions