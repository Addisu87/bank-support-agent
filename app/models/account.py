from pydantic import BaseModel, ConfigDict
from typing import List
import datetime

class Transaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    currency: str ="USD"
    transaction_type: str
    merchant: str
    description: str
    timestamp: datetime.datetime

class Account(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str | None = None
    balance: float
    currency: str
    account_type: str = "checking"
    transactions: List[Transaction] = []

class AccountQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)
        
    user_id: int
    request: str = ""

class AccountResponse(BaseModel):
    balance: str
    recent_transactions: List[str] = []

# ===== API MODELS =====

class CreateAccountRequest(BaseModel):
    """Request model for creating new accounts"""
    email: str
    account_type: str = "checking"
    initial_balance: float = 0.0

class AccountCreationResponse(BaseModel):
    """Response for account creation"""
    status: str
    message: str
    account_number: str | None = None
    account_type: str | None = None
    balance: float | None = None
    currency: str | None = None
    created_at: str | None = None

class AccountInfo(BaseModel):
    """Account information model for API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int | None = None
    account_number: str
    balance: float
    currency: str
    account_type: str
    created_at: str | None = None
