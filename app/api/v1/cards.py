from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.schemas.card import CardCreate, CardResponse, CardUpdate
from app.services.account_service import get_account_by_id
from app.services.card_service import (
    block_card,
    create_card,
    delete_card,
    get_card_by_id,
    get_card_transactions,
    get_user_cards,
    unblock_card,
    update_card,
    update_card_daily_limit,
)
from app.services.email_service import send_email

router = APIRouter(tags=["cards"])


@router.post("/{account_id}", response_model=CardResponse)
async def create_new_card(
    background_tasks: BackgroundTasks,
    account_id: int,
    card_data: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new card for an account"""
    card = await create_card(db, account_id, card_data, current_user.id)
    background_tasks.add_task(
        send_email,
        str(current_user.email),
        "card_created",
        {
            "user_name": str(current_user.full_name),
            "card_type": card.card_type.value,
            "last_four_digits": card.card_number[-4:],
            "expiry_date": card.expiry_date.strftime("%m/%Y"),
        },
    )
    return card


@router.get("/", response_model=List[CardResponse])
async def get_my_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all cards for current user"""
    cards = await get_user_cards(db, current_user.id)
    return cards


@router.get("/{card_id}", response_model=CardResponse)
async def get_card_details(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific card details"""
    card = await get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )

    # Verify card belongs to user
    account = await get_account_by_id(db, card.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this card",
        )

    return card


@router.get("/{card_id}/transactions")
async def get_card_transactions_history(
    card_id: int,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get transactions for a specific card"""
    transactions = await get_card_transactions(db, card_id, current_user.id, limit)
    return transactions


@router.put("/{card_id}", response_model=CardResponse)
async def update_card_details(
    card_id: int,
    card_data: CardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update card details"""
    card = await update_card(db, card_id, card_data, current_user.id)
    return card


@router.put("/{card_id}/limit", response_model=CardResponse)
async def update_card_limit(
    card_id: int,
    new_limit: float = Query(..., gt=0, description="New daily limit"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update card daily limit"""
    card = await update_card_daily_limit(db, card_id, new_limit, current_user.id)
    return card


@router.post("/{card_id}/block", response_model=CardResponse)
async def block_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Block a card"""
    card = await block_card(db, card_id, current_user.id)
    return card


@router.post("/{card_id}/unblock", response_model=CardResponse)
async def unblock_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Unblock a card"""
    card = await unblock_card(db, card_id, current_user.id)
    return card


@router.delete("/{card_id}")
async def delete_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a card"""
    await delete_card(db, card_id, current_user.id)
    return {"message": "Card deleted successfully"}
