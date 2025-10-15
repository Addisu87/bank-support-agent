from typing import Annotated

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.services.user_service import get_user_by_email, update_access_token
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import settings

import logfire
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

# Declaring OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

async def authenticate_user(email: str, password: str): 
    """Authenticate a user by email and password"""
    logfire.debug("Authenticate user", extra={"email": email})
    
    user = await get_user_by_email(email)
    
    if not user: 
        raise credentials_exception("Invalid email or password.")
    if not verify_password(password, user.password):
        raise credentials_exception("Invalid email or password.")
    return user

async def issue_tokens_for_user(user):
    access = create_access_token(user.email, user.roles or [])
    refresh = create_refresh_token(user.email)
    await update_access_token(user.id, refresh)
    return access, refresh

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = jwt.decode(token,
                         settings.JWT_SECRET,
                         settings.ALGORITHM
                        )
    email = payload.get("sub")
    
    if email is None: 
        raise credentials_exception("Token is missing 'sub' field")
    
    user = await get_user_by_email(email=email)
    if user is None: 
        raise credentials_exception("Could not find user for this token")
    return user
    