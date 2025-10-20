import enum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class CardType(enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    PREPAID = "prepaid"


class CardStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOST = "lost"
    STOLEN = "stolen"
    EXPIRED = "expired"
    BLOCKED = "blocked"


class Card(BaseModel):
    __tablename__ = "cards"

    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    bank_id = Column(
        Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False
    )
    card_number = Column(String(16), unique=True, index=True, nullable=False)
    card_holder_name = Column(String(255), nullable=False)
    card_type = Column(SQLEnum(CardType), nullable=False)
    status = Column(SQLEnum(CardStatus), default=CardStatus.ACTIVE, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    cvv = Column(String(3), nullable=False)
    daily_limit = Column(Float, default=1000.0)  # Daily withdrawal/spend limit
    contactless_enabled = Column(Boolean, default=True)
    international_usage = Column(Boolean, default=False)

    # Relationships
    account = relationship("Account", back_populates="cards")
    issuing_bank = relationship("Bank", back_populates="issued_cards")
    transactions = relationship("Transaction", back_populates="card")

    def __repr__(self):
        return f"<Card(id={self.id}, number=****{self.card_number[-4:]}, type={self.card_type})>"
