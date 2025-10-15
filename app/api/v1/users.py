from fastapi import APIRouter, HTTPException, status, Depends

from app.models.user import UserIn, UserResponse
from app.db.models import User
from app.services.user_service import delete_user, list_users, get_user_by_id, update_user
from app.core.deps import get_current_user
from app.services.account_service import get_accounts_by_user

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
async def list_all_users(current_user: User = Depends(get_current_user)):
    """Get a list of all users (admin only)."""
    # In a real application, you would add role-based access control here
    # For now, any authenticated user can list all users.
    users = await list_users()
    return [UserResponse.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    """Get user information by user ID or 'me' for the current user."""
    if user_id == "me":
        return UserResponse.model_validate(current_user)

    # Convert user_id to int for database query
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")

    # Basic authorization check: A user can only view their own profile
    # unless they have an 'admin' role (not implemented yet).
    if user_id_int != current_user.id: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user's information")

    user = await get_user_by_id(user_id_int)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return UserResponse.model_validate(user)

        
@router.get("/{user_id}/accounts")
async def user_accounts(user_id: int, current_user: User = Depends(get_current_user)):
    """Get all accounts for a user by user ID."""
    # Basic authorization check: A user can only view their own accounts
    # unless they have an 'admin' role (not implemented yet).
    if user_id != current_user.id: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user's accounts")
    accounts = await get_accounts_by_user(user_id)
    if not accounts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No accounts found for this user')
    
    return [{
        "id": acc.id, 
        "account_number": acc.account_number, 
        "balance": acc.balance, 
        "currency": acc.currency,
        "account_type": acc.account_type
    } for acc in accounts]

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(user_id: int, user_in: UserIn, current_user: User = Depends(get_current_user)):
    """Update a user's profile by user ID."""
    # Basic authorization check: A user can only update their own profile
    # unless they have an 'admin' role (not implemented yet).
    if user_id != current_user.id: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user's information")

    db_user = await get_user_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = await update_user(db_user=db_user, user_in=user_in)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(user_id: int, current_user: User = Depends(get_current_user)):
    """Delete a user by their ID."""
    # Basic authorization check: A user can only delete their own account
    # unless they have an 'admin' role (not implemented yet).
    if user_id != current_user.id: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user's account")
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deleted successfully"}

