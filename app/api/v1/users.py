from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user import UserBase, UserResponse
from app.db.schema import User
from app.core.deps import get_current_active_user
from app.db.session import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
async def get_users(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_session)):
    """Get a list of all users (admin only)."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    if user_id != current_user.id: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user's information")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_in: UserBase,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Update a user's profile by user ID."""
    if user_id != current_user.id: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's information"
        )

    db_user = await db.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Update only the allowed fields
    user_data = user_in.model_dump(exclude_unset=True)
    
    if user_data.get("password"):
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        
    for field, value in user_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserResponse.model_validate(db_user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Delete a user by their ID."""
    if user_id != current_user.id: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user's account")
    
    db_user = await db.get(User, user_id)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not found"
        )

    await db.delete(db_user)
    await db.commit()
    return {"message", "User deleted!"}  # FIXED: 204 should return no content