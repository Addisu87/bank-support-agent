# User model + Pydantic schema
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import datetime
from typing import List

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    
class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email: str 
    password: str
    
class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr | None = None
    full_name: str | None = None
    phone_number: str | None = None

class UserResponse(UserBase):
    """User information response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    roles: List[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime | None = None

class Token(BaseModel):
    """Token"""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    token_type: str 

class TokenData(BaseModel):
    email: str | None = None