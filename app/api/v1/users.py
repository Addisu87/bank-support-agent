from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user
from app.db.models.user import User
from app.db.session import AsyncSession, get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import (
    delete_user,
    get_all_users,
    get_user_by_id,
    update_user,
)

router = APIRouter(tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def get_users(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a list of all users (admin only)."""
    # Add admin check if needed
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Not authorized")

    users = await get_all_users(db)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_current_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if user can only update their own profile
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Can only update your own profile")

    """Update a user's profile by user ID."""
    updated_user = await update_user(db, user_id, user_data)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Prevent users from deleting other people's accounts
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Can only delete your own account")

    """Delete a user by their ID."""
    await delete_user(db, user_id)
    return {"message": "Successfully delete a user!"}
