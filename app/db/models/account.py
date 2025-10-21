import enum

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class AccountType(enum.Enum):
    SAVINGS = "savings"
    CHECKING = "checking"
    BUSINESS = "business"
    LOAN = "loan"
    CREDIT = "credit"


class AccountStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Account(BaseModel):
    __tablename__ = "accounts"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bank_id = Column(
        Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False
    )
    account_number = Column(String(50), unique=True, nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    available_balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    overdraft_limit = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="accounts")
    bank = relationship("Bank", back_populates="accounts")
    transactions = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )
    cards = relationship("Card", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(id={self.id}, number={self.account_number}, balance={self.balance})>"
