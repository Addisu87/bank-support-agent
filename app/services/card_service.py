import uuid
from datetime import datetime, timedelta

import logfire
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.db.models.account import Account
from app.db.models.bank import Bank
from app.db.models.card import Card, CardStatus
from app.schemas.card import CardCreate, CardUpdate

# ------------------------
# 🔧 Utility Functions
# ------------------------


def generate_card_number(bank_code: str) -> str:
    """Generate valid card number using Luhn algorithm"""
    # Start with bank-specific prefix
    if bank_code == "DEMO":
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
    with logfire.span("get_card_by_id", card_id=card_id):
        cache_key = f"card:{card_id}"
        cached = await cache.get_json(cache_key)
        if cached:
            return Card(**cached)

        card = await db.get(Card, card_id)
        if card:
            await cache.set_json(cache_key, card.__dict__)
        return card


async def get_card_by_number(db: AsyncSession, card_number: str) -> Card:
    with logfire.span("get_card_by_number", card_number=card_number[-4:]):
        cache_key = f"card:number:{card_number}"
        cached = await cache.get_json(cache_key)
        if cached:
            return Card(**cached)

        result = await db.execute(select(Card).filter(Card.card_number == card_number))
        card = result.scalar_one_or_none()
        if card:
            await cache.set_json(cache_key, card.__dict__)
        return card


async def get_user_cards(db: AsyncSession, user_id: int) -> list[Card]:
    with logfire.span("get_user_cards", user_id=user_id):
        cache_key = f"user_cards:{user_id}"
        cached = await cache.get_json(cache_key)
        if cached:
            return [Card(**card_data) for card_data in cached]

        result = await db.execute(
            select(Card)
            .join(Account)
            .filter(Account.user_id == user_id)
            .filter(Card.status != CardStatus.EXPIRED)
        )
        cards = result.scalars().all()
        await cache.set_json(cache_key, [card.__dict__ for card in cards])
        return cards


async def create_card(
    db: AsyncSession, account_id: int, card_data: CardCreate, user_id: int
) -> Card:
    with logfire.span("create_card", account_id=account_id):
        # Verify account exists and belongs to user
        account = await db.get(Account, account_id)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
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

        card = Card(
            account_id=account_id,
            bank_id=account.bank_id,
            card_number=card_number,
            cvv=cvv,
            expiry_date=expiry_date,
            card_holder_name=card_data.card_holder_name,
            card_type=card_data.card_type,
            daily_limit=card_data.daily_limit,
            contactless_enabled=card_data.contactless_enabled,
            international_usage=card_data.international_usage,
        )

        db.add(card)
        await db.commit()
        await db.refresh(card)

        # Clear cache
        await cache.clear_pattern(f"user_cards:{user_id}")

        return card


async def update_card(
    db: AsyncSession, card_id: int, card_data: CardUpdate, user_id: int
) -> Card:
    with logfire.span("update_card", card_id=card_id):
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
                detail="Not authorized to update this card",
            )

        update_data = card_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)

        await db.commit()
        await db.refresh(card)

        # Clear cache
        await cache.delete(f"card:{card_id}")
        await cache.delete(f"card:number:{card.card_number}")
        await cache.clear_pattern(f"user_cards:{user_id}")

        return card


async def block_card(db: AsyncSession, card_id: int, user_id: int) -> Card:
    with logfire.span("block_card", card_id=card_id):
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
                detail="Not authorized to block this card",
            )

        card.status = CardStatus.BLOCKED
        await db.commit()
        await db.refresh(card)

        # Clear cache
        await cache.delete(f"card:{card_id}")
        await cache.delete(f"card:number:{card.card_number}")
        await cache.clear_pattern(f"user_cards:{user_id}")

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
        account = await db.get(Account, card.account_id)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to unblock this card",
            )

        if card.status != CardStatus.BLOCKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Card is not blocked"
            )

        card.status = CardStatus.ACTIVE
        await db.commit()
        await db.refresh(card)

        # Clear cache
        await cache.delete(f"card:{card_id}")
        await cache.delete(f"card:number:{card.card_number}")
        await cache.clear_pattern(f"user_cards:{user_id}")

        return card


async def validate_card_transaction(
    db: AsyncSession, card_number: str, amount: float, merchant: str = None
) -> bool:
    """Validate if card can be used for transaction"""
    with logfire.span(
        "validate_card_transaction", card_number=card_number[-4:], amount=amount
    ):
        card = await get_card_by_number(db, card_number)
        if not card:
            return False

        # Check card status
        if card.status != CardStatus.ACTIVE:
            return False

        # Check expiry
        if card.expiry_date < datetime.now():
            card.status = CardStatus.EXPIRED
            await db.commit()
            return False

        # Check daily limit (simplified - in production, track daily usage)
        if amount > card.daily_limit:
            return False

        # Check international usage
        if (
            merchant
            and "international" in merchant.lower()
            and not card.international_usage
        ):
            return False

        return True


# ------------------------
# 🔧 Additional Card Functions
# ------------------------


async def delete_card(db: AsyncSession, card_id: int, user_id: int) -> bool:
    """Delete a card (soft delete by setting status to inactive)"""
    with logfire.span("delete_card", card_id=card_id):
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
                detail="Not authorized to delete this card",
            )

        card.status = CardStatus.INACTIVE
        await db.commit()

        # Clear cache
        await cache.delete(f"card:{card_id}")
        await cache.delete(f"card:number:{card.card_number}")
        await cache.clear_pattern(f"user_cards:{user_id}")

        return True


async def update_card_daily_limit(
    db: AsyncSession, card_id: int, new_limit: float, user_id: int
) -> Card:
    """Update card daily spending limit"""
    with logfire.span("update_card_daily_limit", card_id=card_id, new_limit=new_limit):
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
                detail="Not authorized to update this card",
            )

        if new_limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily limit must be positive",
            )

        card.daily_limit = new_limit
        await db.commit()
        await db.refresh(card)

        # Clear cache
        await cache.delete(f"card:{card_id}")
        await cache.delete(f"card:number:{card.card_number}")

        return card


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
        account = await db.get(Account, card.account_id)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this card's transactions",
            )

        from app.services.transaction_service import get_card_transactions as get_txns

        return await get_txns(db, card_id, limit)


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

        # Clear cache
        await cache.delete(f"card:{card_id}")
        await cache.delete(f"card:number:{card.card_number}")
        await cache.clear_pattern(f"user_cards:{user_id}")

        return card
