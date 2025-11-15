from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.core.security import create_access_token
from app.db.models.user import User
from app.db.session import AsyncSession, get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.user_service import (
    authenticate_user,
    change_user_password,
    create_user,
)
from app.services.email_service import send_email

router = APIRouter(tags=["authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    background_tasks: BackgroundTasks,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    user_db = await create_user(db, user_data)

    # Send welcome email directly
    background_tasks.add_task(
        send_email,
        str(user_db.email),
        "user_welcome",  # template_type
        {"user_name": str(user_db.full_name)},  # template_data
    )
    return UserResponse.model_validate(user_db)


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password"""
    success = await change_user_password(
        db, current_user.id, current_password, new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return {"message": "Password updated successfully"}
