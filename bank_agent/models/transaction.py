"""
Transaction related models
"""
from pydantic import BaseModel, ConfigDict
import datetime

class Transaction(BaseModel):
    """Core transaction model"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    currency: str
    transaction_type: str
    description: str
    merchant: str | None
    timestamp: datetime.datetime

class TransactionInfo(BaseModel):
    """Transaction information model for API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int | None = None
    amount: float
    currency: str
    transaction_type: str
    description: str
    merchant: str | None = None
    timestamp: str

class TransactionRequest(BaseModel):
    """Request model for transaction queries"""
    user_email: str
    account_number: str
    limit: int = 5