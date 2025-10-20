from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.db.models.account import AccountStatus, AccountType


class AccountBase(BaseModel):
    account_type: AccountType
    currency: str = "USD"


class AccountCreate(AccountBase):
    bank_id: int


class AccountUpdate(BaseModel):
    status: str | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bank_id: int
    bank_name: str
    account_number: str
    available_balance: float
    status: AccountStatus
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def from_orm(cls, obj):
        # Custom from_orm to include bank name
        data = super().from_orm(obj)
        data.bank_name = obj.bank.name if obj.bank else "Unknown"
        return data


class AccountBalance(BaseModel):
    account_number: str
    balance: str
    currency: str


class TransferRequest(BaseModel):
    from_account_number: str
    to_account_number: str
    amount: float
    description: str = "Fund transfer"

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
