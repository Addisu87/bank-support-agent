from fastapi import APIRouter, HTTPException, status
from ..models.user import UserIn, UserLogin
from bank_agent.db.storage import get_user_by_email
from bank_agent.core.deps import register_user, issue_tokens_for_user
from bank_agent.core.security import verify_password

router = APIRouter()

@router.post("/auth/register", status_code=201)
async def register( user: UserIn):
    
    existing_user = await get_user_by_email(email=user.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists!",
        )
    
    await register_user(user.email, user.password)
    return {"status": "registered"}
    
    
@router.post("/auth/login")
async def login(user: UserLogin):
    db_user = await get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access, refresh = await issue_tokens_for_user(db_user)
    return {"access_token": access, "refresh_token": refresh}

    
    
    
    