from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserUpdate, UserResponse
from app.db.models.user import User
from app.core.deps import get_current_active_user
from app.db.session import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.services.user_service import update_user, get_user_by_id, delete_user

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
async def get_users(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a list of all users (admin only)."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_id(db, current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user's profile by user ID."""
    updated_user = await update_user(db, current_user.id, user_data)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user by their ID."""
    return await delete_user(db, current_user.id)
   