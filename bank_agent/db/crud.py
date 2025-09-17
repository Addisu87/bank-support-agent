# CRUD operations for users, audits, accounts, bank, transactions, card

from bank_agent.db.models import(Base, User, Audit, Account, Bank, Transaction, Card)
from bank_agent.db.postgres import engine, AsyncSessionLocal
from sqlalchemy import select
from bank_agent.core.security import hash_password
from bank_agent.models.user import UserIn
import datetime
import random

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
    
async def create_bank(name: str, bic: str = None, country: str = None):
    async with AsyncSessionLocal() as session: 
        bank = Bank(name=name, bic=bic, country=country)
        session.add(bank)
        await session.commit()
        await session.refresh(bank)
        return bank
    
async def create_account(user_id: int, bank_id: int, account_number: str = None, balance: float = 0.0, currency: str ="USD", account_type: str = "checking"):
    async with AsyncSessionLocal() as session: 
        if account_number is None: 
            account_number = f"ACCT{int(datetime.datetime.timezone.utcnow().timestamp())}{random.randint(1000, 9999)}"
        account = Account(user_id=user_id, bank_id=bank_id, account_number=account_number, balance=balance, currency=currency, account_type=account_type)
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account
    
    
async def get_accounts_by_user(user_id: int):
    async with AsyncSessionLocal() as session: 
        result = await session.execute(select(Account).filter_by(user_id=user_id))
        return result.scalars().all()
    

async def create_transaction(account_id: int, amount: float, currency: str, transaction_type: str = "payment", description: str = "", merchant: str = None):
    async with AsyncSessionLocal() as session: 
        tx = Transaction(account_id=account_id, amount=amount, currency=currency, transaction_type=transaction_type, description=description, merchant=merchant)
        session.add(tx)
        # update account balance
        acct = await session.get(Account, account_id)
        if acct: 
            acct.balance = (acct.balance or 0.0) + amount
            session.add(acct)
        await session.commit()
        await session.refresh(tx)
        return tx
    
async def get_transactions(account_id: int, limit: int = 10):
    async with AsyncSessionLocal() as session: 
        result = await session.execute(select(Transaction).filter_by(account_id=account_id).order_by(Transaction.timestamp.desc()).limit(limit))
        return result.scalars().all()
    
async def create_card(account_id: int, card_number: str, card_type: str = "debit", expiry_date = None):
    async with AsyncSessionLocal() as session: 
        card = Card(account_id=account_id, card_number=card_number, card_type=card_type, expiry_date=expiry_date)
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return Card
    
async def get_card_by_number(card_number: str):
    """Get a card by its card number."""
    async with AsyncSessionLocal() as session: 
        result = await session.execute(select(Card).filter_by(card_number=card_number))
        return result.scalar_one_or_none()

async def get_cards_by_user(user_id: int):
    """Get all cards for a user."""
    async with AsyncSessionLocal() as session: 
        result = await session.execute(
            select(Card).join(Account).filter(Account.user_id == user_id)
        )
        return result.scalars().all()

async def block_card_by_id(card_id: int):
    """Block a card by its ID."""
    async with AsyncSessionLocal() as session: 
        card = await session.get(Card, card_id)
        if not card: 
            return None 
        card.status = "blocked"
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return card

async def block_card_by_number(card_number: str, user_id: int):
    """Block a card by its number, ensuring it belongs to the user."""
    async with AsyncSessionLocal() as session: 
        # Join Card with Account to ensure the card belongs to the user
        result = await session.execute(
            select(Card).join(Account).filter(
                Card.card_number == card_number,
                Account.user_id == user_id
            )
        )
        card = result.scalar_one_or_none()
        
        if not card: 
            return None 
        
        if card.status == "blocked":
            return {"already_blocked": True, "card": card}
            
        card.status = "blocked"
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return {"already_blocked": False, "card": card}