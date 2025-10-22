import uuid
from datetime import datetime, timedelta

import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.account import Account
from app.db.models.bank import Bank
from app.db.models.card import Card, CardStatus
from app.db.models.transaction import Transaction
from app.schemas.card import CardCreate, CardUpdate

# ------------------------
# 🔧 Utility Functions
# ------------------------


def generate_card_number(bank_code: str) -> str:
    """Generate valid card number using Luhn algorithm"""
    # Start with bank-specific prefix
    if bank_code == "AB":
        prefix = "4111"  # Visa-like
    else:
        prefix = "5111"  # Mastercard-like

    # Generate random digits
    base = prefix + "".join([str(uuid.uuid4().int % 10) for _ in range(11)])

    # Calculate Luhn check digit
    total = 0
    for i, digit in enumerate(reversed(base)):
        n = int(digit)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    check_digit = (10 - (total % 10)) % 10
    return base + str(check_digit)


def generate_cvv() -> str:
    """Generate 3-digit CVV"""
    return f"{uuid.uuid4().int % 1000:03d}"


def generate_expiry_date(years: int = 3) -> datetime:
    """Generate expiry date (default 3 years from now)"""
    return datetime.now() + timedelta(days=365 * years)


# ------------------------
# 🃏 Card CRUD Functions
# ------------------------


async def get_card_by_id(db: AsyncSession, card_id: int) -> Card:
    """Get card by ID"""
    with logfire.span("get_card_by_id", card_id=card_id):
        card = await db.get(Card, card_id)
        return card


async def get_card_by_number(db: AsyncSession, card_number: str) -> Card:
    """Get card by card number"""
    with logfire.span("get_card_by_number", card_number=card_number[-4:]):
        result = await db.execute(select(Card).filter(Card.card_number == card_number))
        card = result.scalar_one_or_none()
        return card


async def get_user_cards(db: AsyncSession, user_id: int) -> list[Card]:
    """Get all cards for a user"""
    with logfire.span("get_user_cards", user_id=user_id):
        result = await db.execute(
            select(Card)
            .join(Account)
            .filter(Account.user_id == user_id)
            .filter(Card.status != CardStatus.EXPIRED)
        )
        cards = result.scalars().all()
        return cards


async def _verify_card_ownership(db: AsyncSession, card: Card, user_id: int) -> None:
    """Helper to verify card belongs to user"""
    account = await db.get(Account, card.account_id)
    if not account or account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this card",
        )


async def create_card(
    db: AsyncSession, account_id: int, card_data: CardCreate, user_id: int
) -> Card:
    """Create a new card for an account"""
    with logfire.span("create_card", account_id=account_id, user_id=user_id):
        # Verify account exists and belongs to user
        account = await db.get(Account, account_id)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        if account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create card for this account",
            )

        # Get bank to generate proper card number
        bank = await db.get(Bank, account.bank_id)
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found"
            )

        # Generate card details
        card_number = generate_card_number(bank.code)
        cvv = generate_cvv()
        expiry_date = generate_expiry_date()

        # Check for card number collision
        existing_card = await get_card_by_number(db, card_number)
        if existing_card:
            card_number = generate_card_number(bank.code)

        # Use model_dump() for concise code
        card_kwargs = {
            **card_data.model_dump(),
            "account_id": account_id,
            "bank_id": account.bank_id,
            "card_number": card_number,
            "cvv": cvv,
            "expiry_date": expiry_date,
            "status": CardStatus.ACTIVE,
        }

        card = Card(**card_kwargs)
        db.add(card)
        await db.commit()
        await db.refresh(card)

        return card


async def update_card(
    db: AsyncSession, card_id: int, card_data: CardUpdate, user_id: int
) -> Card:
    """Update card details"""
    with logfire.span("update_card", card_id=card_id):
        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        await _verify_card_ownership(db, card, user_id)

        update_data = card_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)

        await db.commit()
        await db.refresh(card)

        return card


async def block_card(db: AsyncSession, card_id: int, user_id: int) -> Card:
    """Block a card"""
    with logfire.span("block_card", card_id=card_id):
        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        await _verify_card_ownership(db, card, user_id)
        card.status = CardStatus.BLOCKED
        await db.commit()
        await db.refresh(card)

        return card


async def unblock_card(db: AsyncSession, card_id: int, user_id: int) -> Card:
    """Unblock a previously blocked card"""
    with logfire.span("unblock_card", card_id=card_id):
        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        await _verify_card_ownership(db, card, user_id)

        if card.status != CardStatus.BLOCKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Card is not blocked"
            )

        card.status = CardStatus.ACTIVE
        await db.commit()
        await db.refresh(card)

        return card


async def update_card_daily_limit(
    db: AsyncSession, card_id: int, new_limit: float, user_id: int
) -> Card:
    """Update card daily limit"""
    with logfire.span("update_card_daily_limit", card_id=card_id, new_limit=new_limit):
        if new_limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily limit must be positive",
            )

        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        await _verify_card_ownership(db, card, user_id)
        card.daily_limit = new_limit

        await db.commit()
        await db.refresh(card)
        return card


async def delete_card(db: AsyncSession, card_id: int, user_id: int) -> bool:
    """Delete a card (soft delete by setting status to inactive)"""
    with logfire.span("delete_card", card_id=card_id):
        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        await _verify_card_ownership(db, card, user_id)
        card.status = CardStatus.INACTIVE

        await db.commit()

        return True


# ------------------------
# 🔧 Additional Card Functions
# ------------------------


async def get_card_transactions(
    db: AsyncSession, card_id: int, user_id: int, limit: int = 10
) -> list:
    """Get recent transactions for a specific card"""
    with logfire.span("get_card_transactions", card_id=card_id, limit=limit):
        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        await _verify_card_ownership(db, card, user_id)

        # Direct database query for card transactions
        result = await db.execute(
            select(Transaction)
            .filter(Transaction.card_id == card_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def report_card_lost_or_stolen(
    db: AsyncSession, card_id: int, user_id: int, reason: str
) -> Card:
    """Report a card as lost or stolen"""
    with logfire.span("report_card_lost_stolen", card_id=card_id, reason=reason):
        card = await get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
            )

        # Verify card belongs to user
        account = await db.get(Account, card.account_id)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to report this card",
            )

        if reason.lower() == "lost":
            card.status = CardStatus.LOST
        elif reason.lower() == "stolen":
            card.status = CardStatus.STOLEN
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason must be 'lost' or 'stolen'",
            )

        await db.commit()
        await db.refresh(card)

        return card
