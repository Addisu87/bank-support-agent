from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import List

class BankBase(BaseModel):
    name: str
    code: str 
    swift_code: str | None = None
    routing_number: str | None = None
    country: str
    currency: str = 'USD'
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    address: str | None = None

class BankCreate(BankBase):
    """Bank information model"""
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('code')
    def code_uppercase(cls, v):
        return v.upper()
    
    @field_validator('swift_code')
    def swift_code_uppercase(cls, v):
        return v.upper() if v else v
    
   
class BankUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
        
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    address: str | None = None
    is_active: bool | None = None
    
class BankResponse(BankBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None 
    
class BankListResponse(BaseModel):
    banks: List[BankResponse]
    total: int
