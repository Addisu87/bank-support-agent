from fastapi import APIRouter, HTTPException, status
from bank_agent.db.crud import get_user_by_id, get_accounts_by_user
from bank_agent.models.user import UserResponse

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user information by user ID."""
    user = await get_user_by_id(user_id)
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return UserResponse(
        id=user.id, 
        email=user.email, 
        full_name=user.full_name,
        roles=user.roles or [],
        created_at=user.created_at.isoformat() if user.created_at else None
    )

        
@router.get("/{user_id}/accounts")
async def user_accounts(user_id: int):
    """Get all accounts for a user by user ID."""
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
