from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.db.models.account import AccountStatus, AccountType
from typing import Any


class AccountBase(BaseModel):
    account_type: AccountType
    currency: str = "USD"


class AccountCreate(AccountBase):
    bank_id: int


class AccountUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
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
    
    # Add method to populate bank information from the relationship
    @model_validator(mode='before')
    @classmethod
    def inject_bank_data(cls, data: Any) -> Any:
        if hasattr(data, 'bank') and data.bank:
            return {
                **data.__dict__,
                'bank_name': data.bank.name,
                'bank_code': data.bank.code
            }
        return data


class AccountBalance(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    account_number: str
    balance: float
    available_balance: float
    currency: str

class AccountCreateResponse(BaseModel):
    message: str
    account: AccountResponse
