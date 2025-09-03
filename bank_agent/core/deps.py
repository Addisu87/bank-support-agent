from typing import List

from bank_agent.db.storage import get_user_by_email, create_user, update_access_token
from bank_agent.core.security import verify_password, hash_password,create_access_token, create_refresh_token


async def authenticate_user(email: str, password: str): 
    """Authenticate a user by email and password"""
    user = await get_user_by_email(email)
    
    if not user: 
        return None
    
    if not verify_password(password, user.password):
        return None
        
    return user
    
    
async def register_user(email: str, password: str, roles: List[str] | None = None):
    hashed_password = hash_password(password)
    return await create_user(email, hashed_password, name=None, roles=roles or [])

async def issue_tokens_for_user(user):
    access = create_access_token(user.email, user.roles or [])
    refresh = create_refresh_token(user.email)
    await update_access_token(user.id, refresh)
    return access, refresh