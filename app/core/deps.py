from typing import Annotated

import logfire
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import verify_token
from app.db.models.user import User
from app.db.session import AsyncSession, get_db
from app.services.user_service import get_user_by_email

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


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
) -> User:
    token_data = verify_token(token)
    user = await get_user_by_email(db, token_data.email)

    if user is None:
        raise credentials_exception("Could not find user for this token")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not bool(current_user.is_active):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inactive user"
        )
    return current_user
