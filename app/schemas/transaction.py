from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.db.models.transaction import TransactionType, TransactionStatus

class TransactionBase(BaseModel):
    amount: float
    transaction_type: TransactionType
    description: str | None = None
    
class TransactionCreate(TransactionBase):
    """Core transaction model"""
    model_config = ConfigDict(from_attributes=True)
    account_id: int
    reference: str | None = None

class TransactionResponse(TransactionBase):
    """Transaction information model for API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    reference: str
    status: TransactionStatus
    merchant: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

class TransactionQuery(BaseModel):
    """Request model for transaction queries"""
    account_id: int | None = None
    transaction_type: TransactionType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 50
    offset: int = 0

class TransferRequest(BaseModel):
    """Request model for fund transfers"""
    from_account_number: str
    to_account_number: str
    amount: float
    description: str | None = "Fund transfer"