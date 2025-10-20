from typing import Annotated, cast
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_token, verify_password
from app.core.config import settings
from app.db.models.user import User
from app.db.session import AsyncSession
from sqlalchemy import select
from app.db.session import get_db

import logfire
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

# Declaring OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
    
async def get_user(email: str | None, db: AsyncSession):
    """Fetch user from the database."""
    if email is None:
        return None
    query = await db.execute(select(User).filter_by(email=email))
    return query.scalar_one_or_none()

async def authenticate_user(
    email: str,
    password: str,  
    db: AsyncSession
): 
    """Authenticate a user by email and password"""
    logfire.debug("Authenticate user", extra={"email": email})
    
    user = await get_user(email, db)

    if not user: 
        raise credentials_exception("Invalid email or password.")
    
    if not verify_password(password, cast(str, user.hashed_pwd)): 
        raise credentials_exception("Invalid email or password.")
    return user

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> User:
    token_data = verify_token(token)
    user = await get_user(email=token_data.email, db=db)

    if user is None:
        raise credentials_exception("Could not find user for this token")
    return user
    
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    if not bool(current_user.is_active): 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inactive user"
        )
    return current_user