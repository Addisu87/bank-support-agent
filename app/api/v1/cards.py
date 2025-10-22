from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
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

router = APIRouter(tags=["cards"])


@router.get("/", response_model=List[CardResponse])
async def get_my_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all cards for current user"""
    try:
        cards = await get_user_cards(db, current_user.id)
        return cards
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching cards: {str(e)}",
        )


@router.post("/{account_id}", response_model=CardResponse)
async def create_new_card(
    account_id: int,
    card_data: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new card for an account"""
    try:
        card = await create_card(db, account_id, card_data, current_user.id)
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating card: {str(e)}",
        )


@router.get("/{card_id}", response_model=CardResponse)
async def get_card_details(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific card details"""
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching card: {str(e)}",
        )


@router.get("/{card_id}/transactions")
async def get_card_transactions_history(
    card_id: int,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get transactions for a specific card"""
    try:
        transactions = await get_card_transactions(db, card_id, current_user.id, limit)
        return transactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching card transactions: {str(e)}",
        )


@router.put("/{card_id}", response_model=CardResponse)
async def update_card_details(
    card_id: int,
    card_data: CardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update card details"""
    try:
        card = await update_card(db, card_id, card_data, current_user.id)
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating card: {str(e)}",
        )


@router.put("/{card_id}/limit", response_model=CardResponse)
async def update_card_limit(
    card_id: int,
    new_limit: float = Query(..., gt=0, description="New daily limit"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update card daily limit"""
    try:
        card = await update_card_daily_limit(db, card_id, new_limit, current_user.id)
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating card limit: {str(e)}",
        )


@router.post("/{card_id}/block", response_model=CardResponse)
async def block_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Block a card"""
    try:
        card = await block_card(db, card_id, current_user.id)
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error blocking card: {str(e)}",
        )


@router.post("/{card_id}/unblock", response_model=CardResponse)
async def unblock_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Unblock a card"""
    try:
        card = await unblock_card(db, card_id, current_user.id)
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unblocking card: {str(e)}",
        )


@router.delete("/{card_id}")
async def delete_user_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a card"""
    try:
        await delete_card(db, card_id, current_user.id)
        return {"message": "Card deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting card: {str(e)}",
        )
