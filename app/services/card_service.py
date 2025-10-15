from app.db.models import Card, Account
from app.db.postgres import AsyncSessionLocal
from sqlalchemy import select

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