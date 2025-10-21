from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.account import AccountStatus, AccountType


class AccountBase(BaseModel):
    account_type: AccountType
    currency: str = "USD"


class AccountCreate(AccountBase):
    bank_id: int


class AccountUpdate(BaseModel):
    status: AccountStatus | None = None
    account_type: AccountType | None = None
    balance: float | None = None
    available_balance: float | None = None
    currency: str | None = None
    overdraft_limit: float | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bank_id: int
    bank_name: str | None = None
    bank_code: str | None = None
    account_number: str
    account_type: AccountType
    balance: float
    available_balance: float
    currency: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime | None = None


class AccountBalance(BaseModel):
    account_number: str
    balance: float
    available_balance: float
    currency: str


class AccountCreateResponse(BaseModel):
    message: str
    account: AccountResponse
