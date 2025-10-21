from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.account import AccountStatus, AccountType
from app.schemas.bank import BankResponse


class AccountBase(BaseModel):
    account_type: AccountType
    currency: str = "USD"


class AccountCreate(AccountBase):
    bank_id: int


class AccountUpdate(BaseModel):
    status: AccountStatus | None = None
    account_type: AccountType | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bank_id: int
    bank_name: str
    account_number: str
    account_type: AccountType
    balance: float
    available_balance: float
    currency: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime | None = None
    bank = BankResponse


class AccountBalance(BaseModel):
    account_number: str
    balance: float
    available_balance: float
    currency: str


class AccountCreateResponse(BaseModel):
    message: str
    account: AccountResponse
