import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    """Get user by email"""
    with logfire.span("get_user_by_email", email=email):
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    """Get user by ID"""
    with logfire.span("get_user_by_id", user_id=user_id):
        return await db.get(User, user_id)


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user"""
    with logfire.span("create_user", email=user_data.email):
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_pwd=hashed_password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """Authenticate user with email and password"""
    with logfire.span("authenticate_user", email=email):
        user = await get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_pwd):
            return None
        return user


async def change_user_password(
    db: AsyncSession, user_id: int, current_password: str, new_password: str
) -> bool:
    """Change user password"""
    with logfire.span("change_password", user_id=user_id):
        user = await get_user_by_id(db, user_id)
        if not user or not verify_password(current_password, user.hashed_pwd):
            return False

        user.hashed_pwd = get_password_hash(new_password)
        await db.commit()
        return True


async def get_all_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[User]:
    """Get all users with pagination"""
    with logfire.span("get_all_users", skip=skip, limit=limit):
        result = await db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return result.scalars().all()


async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> User:
    """Update user information"""
    with logfire.span("update_user", user_id=user_id):
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
        return user


async def update_user_status(db: AsyncSession, user_id: int, is_active: bool) -> User:
    """Update user active status"""
    with logfire.span("update_user_status", user_id=user_id, is_active=is_active):
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.is_active = is_active  # type: ignore
        await db.commit()
        await db.refresh(user)
        return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete user by ID"""
    with logfire.span("delete_user", user_id=user_id):
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await db.delete(user)
        await db.commit()
        return True
