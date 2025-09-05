# CRUD operations for users, sessions, tickets, messages, documents

from bank_agent.db.models import Base, User, Audit
from bank_agent.db.postgres import engine, AsyncSessionLocal
from sqlalchemy import select
from bank_agent.core.security import hash_password
from bank_agent.models.user import UserIn

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
#  Create user
async def create_user(email, password, full_name=None, roles=None):
    """Create a new user."""
    roles = roles or []
    full_name = full_name or email.split('@')[0]  # Use email prefix as default full_name
    async with AsyncSessionLocal() as session: 
        exists = await session.scalar(select(User).filter_by(email=email))
        if exists: 
            return None 
        db_user = User(full_name=full_name, email=email, password=password, roles=roles)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user 
    
# Get user using email
async def get_user_by_email(email):
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
    
async def save_audit(actor, tool, args, result, request_id=None):
    async with AsyncSessionLocal() as session: 
        aud = Audit(actor=actor, tool=tool, args=str(args), result=str(result), request_id=request_id)
        session.add(aud)
        await session.commit()
        return aud 