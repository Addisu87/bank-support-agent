from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.bank import BankCreate, BankListResponse, BankResponse
from app.services.bank_service import create_bank, get_all_active_banks, get_bank_by_id

router = APIRouter(tags=["banks"])


@router.post("/", response_model=BankCreate, status_code=status.HTTP_201_CREATED)
async def create_new_bank(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new bank.
    """
    bank = await create_bank(db, current_user.id)
    return bank


@router.get("/", response_model=BankListResponse)
async def get_all_banks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    "Get all active banks"
    banks = await get_all_active_banks(db, current_user.id)
    return BankListResponse(banks=banks, total=len(banks))


@router.get("/{bank_id}", response_model=BankResponse)
async def get_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific bank details"""

    bank = await get_bank_by_id(db, bank_id)

    if not bank or not bank.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found"
        )

    return bank
