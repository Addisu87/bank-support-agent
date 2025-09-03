# CRUD operations for users, sessions, tickets, messages, documents

from .models import Base, User, Audit
from .postgres import engine, AsyncSessionLocal
from sqlalchemy import select

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
#  Create user
async def create_user(email, password, name=None, roles=None):
    roles = roles or []
    name = name or email.split('@')[0]  # Use email prefix as default name
    async with AsyncSessionLocal() as session: 
        exists = await session.scalar(select(User).filter_by(email=email))
        if exists: 
            return None 
        user = User(name=name, email=email, password=password, roles=roles)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user 
    
# Get user using email
async def get_user_by_email(email):
    async with AsyncSessionLocal() as session: 
        return await session.scalar(select(User).filter_by(email=email))

# Get user using ID
async def get_user_by_id(user_id):
    async with AsyncSessionLocal() as session: 
        return await session.get(User, user_id)
    
# Update access token
async def update_access_token(user_id, access_token):
    async with AsyncSessionLocal() as session: 
        user = await session.get(User, int(user_id))
        if not user: 
            return False
        user.access_token = access_token
        session.add(user)
        await session.commit()
        return True
    
async def save_audit(actor, tool, args, result, request_id=None):
    async with AsyncSessionLocal() as session: 
        aud = Audit(actor=actor, tool=tool, args=str(args), result=str(result), request_id=request_id)
        session.add(aud)
        await session.commit()
        return aud 