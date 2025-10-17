import logfire
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user import UserRegister, UserLogin, RegisterResponse, UserResponse, PasswordUpdate, Token
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.deps import authenticate_user, get_current_active_user
from app.db.session import AsyncSession
from app.db.session import get_session
from app.db.schema import User
from sqlalchemy import select
from app.utils.constants import access_token_expire_minutes
from datetime import timedelta
from typing import cast

router = APIRouter()

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserRegister,
    db: AsyncSession = Depends(get_session)
):
    """Register a new user account."""
    query = await db.execute(select(User).filter_by(email=user.email))
    existing_user = query.scalar_one_or_none()
    
    if existing_user:
        logfire.info("User already exists!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists!",
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_pwd=hashed_password,
        full_name=user.full_name,
        roles=user.roles,
        is_active=True 
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Return proper response
    return RegisterResponse(
        status="success",
        message="User registered successfully",
        user=UserResponse.model_validate(db_user)
    )

# @router.post("/token", response_model=LoginResponse, status_code=status.HTTP_200_OK)
# async def login(
#     user_data: UserLogin,
#     db: AsyncSession = Depends(get_session)
# ):
#     """Login user and return complete user information with tokens."""
#     auth_user = await authenticate_user(user_data.email, user_data.password, db)
    
#     access_token = create_access_token(auth_user.email)
#     refresh_token = create_refresh_token(auth_user.email) 
#     return LoginResponse(
#         access_token=access_token,
#         refresh_token=refresh_token,
#         token_type="bearer",
#         user=UserResponse.model_validate(auth_user),
#         expires_in=3600
#     )

@router.post("/token")
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_session)
) -> Token:
    user = await authenticate_user(user_data.email, user_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=access_token_expire_minutes())
    access_token = create_access_token(
        data={"sub": user_data.email},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")
    
@router.patch("/{user_id}/password", status_code=status.HTTP_200_OK)
async def update_password(
    user_id: int,
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Update user password."""
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's password"
        )

    db_user = await db.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Verify current password

    if not verify_password(password_data.current_password, cast(str, db_user.hashed_pwd)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update to new password
    db_user.hashed_pwd = get_password_hash(password_data.new_password)  # type: ignore
    await db.commit()
    
    return {"status": "success", "message": "Password updated successfully"}