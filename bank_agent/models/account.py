from pydantic import BaseModel, ConfigDict
from typing import List
import datetime

class Transaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    currency: str
    transaction_type: str
    description: str
    merchant: str | None
    timestamp: datetime.datetime

class Account(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    balance: float
    currency: str
    account_type: str
    transactions: List[Transaction] = []

class AccountQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)
        
    user_id: int
    request: str = ""

class AccountResponse(BaseModel):
    balance: str
    recent_transactions: List[str] = []
