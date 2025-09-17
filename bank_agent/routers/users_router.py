from fastapi import APIRouter, HTTPException, status
from bank_agent.db.crud import get_user_by_id, get_accounts_by_user

router = APIRouter()

@router.get("/{user_id}")
async def get_user(user_id: int):
    user = await get_user_by_id(user_id)
    if not user: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
    return {"id": user.id, "email": user.email, 'full_name': user.full_name}
        
@router.get("/{user_id}/accounts")
async def user_accounts(user_id: int):
    accounts = await get_accounts_by_user(user_id)
    return [{
        "id": acc.id, 
        "account_number": acc.account_number, 
        "balance": acc.balance, 
        "currency": acc.currency
    } for acc in accounts]