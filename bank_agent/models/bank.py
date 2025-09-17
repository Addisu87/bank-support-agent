"""
Bank related models
"""
from pydantic import BaseModel, ConfigDict

class BankInfo(BaseModel):
    """Bank information model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int | None = None
    name: str
    bic: str | None = None
    country: str | None = None

class BankingInfoResponse(BaseModel):
    """Response for banking information queries"""
    bank: BankInfo
    total_banks_available: int | None = None
    demo_accounts: int | None = None
    message: str
