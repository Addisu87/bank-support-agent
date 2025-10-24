from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.db.models.transaction import TransactionStatus, TransactionType


class TransactionBase(BaseModel):
    amount: float
    transaction_type: TransactionType
    description: str | None = None


class TransactionCreate(TransactionBase):
    """Core transaction model"""

    model_config = ConfigDict(from_attributes=True)

    account_id: int
    reference: str | None = None
    card_id: int | None = None


class TransactionResponse(TransactionBase):
    """Transaction information model for API responses"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    reference: str
    status: TransactionStatus
    transfer_id: str | None = None
    merchant: str | None = None
    card_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TransactionQuery(BaseModel):
    """Request model for transaction queries"""

    model_config = ConfigDict(from_attributes=True)

    account_id: int | None = None
    transaction_type: TransactionType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 50
    offset: int = 0


class TransferRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_account_number: str
    to_account_number: str
    amount: float
    description: str = "Fund transfer"

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class DepositRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_number: str
    amount: float
    description: str = "Deposit"

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class WithdrawalRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_number: str
    amount: float
    description: str = "Withdrawal"

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
