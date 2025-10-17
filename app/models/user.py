# User model + Pydantic schema
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    email: EmailStr
    roles: str
    
class UserRegister(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str 
    password: str

class UserResponse(UserBase):
    """User information response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    roles: str
    created_at: datetime | None = None
    is_active: bool

class LoginResponse(BaseModel):
    """Complete login response with user info and tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 3600

class RegisterResponse(BaseModel):
    """Registration response"""
    status: str
    message: str
    user: UserResponse
class Token(BaseModel):
    """Token"""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    token_type: str 

class TokenData(BaseModel):
    email: str | None = None

# ===== REQUEST MODELS =====

class UserEmailRequest(BaseModel):
    """Request model for operations requiring user email"""
    model_config = ConfigDict(from_attributes=True)
    
    email: str 
    
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str