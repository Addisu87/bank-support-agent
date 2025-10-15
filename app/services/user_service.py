from sqlalchemy import select
from app.db.models import User
from app.db.postgres import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import UserIn


#  Create user
async def create_user(email, password, full_name=None, roles=None):
    """Create a new user."""
    roles = roles or []
    full_name = full_name or email.split('@')[0]  # Use email prefix as default full_name
    async with AsyncSessionLocal() as session: 
        # check exists
        exists = await session.scalar(select(User).filter_by(email=email))
        if exists: 
            return None 
        hashed_password = hash_password(password)
        db_user = User( email=email, password=hashed_password, full_name=full_name, roles=roles)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user 
    
# Get user using email
async def get_user_by_email(email: str):
    """Retrieve a user by their email address."""
    async with AsyncSessionLocal() as session: 
        return await session.scalar(select(User).filter_by(email=email))

# Get user using ID
async def get_user_by_id(user_id):
    """Retrieve a user by their ID."""
    async with AsyncSessionLocal() as session: 
        return await session.get(User, user_id)
    
async def update_user(db_user: User, user_in: UserIn):
    """Update user attributes."""
    async with AsyncSessionLocal() as session: 
        user_data = user_in.model_dump(exclude_unset=True)
        if user_data.get("password"):
            user_data["hashed_password"] = hash_password(user_data.pop("password"))
        for field, value in user_data.items():
            setattr(db_user, field, value)

        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user


async def list_users():
    """Retrieve a list of all users."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


async def delete_user(user_id: int) -> bool:
    """Delete a user by their ID."""
    async with AsyncSessionLocal() as session:
        db_user = await session.get(User, user_id)
        if not db_user:
            return False
        await session.delete(db_user)
        await session.commit()
        return True


# Update access token
async def update_access_token(user_id, access_token):
    async with AsyncSessionLocal() as session: 
        db_user = await session.get(User, int(user_id))
        if not db_user: 
            return False
        db_user.access_token = access_token
        session.add(db_user)
        await session.commit()
        return True