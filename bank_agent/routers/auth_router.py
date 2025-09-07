from fastapi import APIRouter, HTTPException, status
import logfire
from ..models.user import UserIn, UserLogin
from bank_agent.db.crud import get_user_by_email
from bank_agent.core.deps import (
    register_user,
    authenticate_user,
    issue_tokens_for_user
)

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register( user: UserIn):
    
    existing_user = await get_user_by_email(email=user.email)
    logfire.info("User already exists!")
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists!",
        )
    
    await register_user(user.email, user.password)
    return {"status": "registered"}
    
    
@router.post("/token")
async def login(form_data: UserLogin):
    logfire.info("User logged in!")
    auth_user = await authenticate_user(form_data.email, form_data.password)
    if not auth_user: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    access, refresh = await issue_tokens_for_user(auth_user)
    return {"access_token": access, "refresh_token": refresh}

    
    
    
    