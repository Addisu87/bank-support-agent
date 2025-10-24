import enum

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    FEE = "fee"


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class Transaction(BaseModel):
    __tablename__ = "transactions"

    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    card_id = Column(
        Integer, ForeignKey("cards.id", ondelete="SET NULL"), nullable=True
    )
    amount = Column(Float, nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(
        SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )
    description = Column(Text)
    reference = Column(String(100), unique=True, index=True)
    transfer_id = Column(String(100), index=True)
    merchant = Column(String(255), nullable=True)
    merchant_category = Column(String(100))  # MCC code category
    location = Column(String(255))

    # Relationships
    account = relationship("Account", back_populates="transactions")
    card = relationship("Card", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"
