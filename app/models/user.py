# User model + Pydantic schema
from pydantic import BaseModel, ConfigDict
from typing import List

class UserRegister(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    email: str 
    
class UserIn(UserRegister):
    password: str

class UserLogin(BaseModel):
    email: str 
    password: str

class UserResponse(BaseModel):
    """User information response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    full_name: str
    roles: List[str] = []
    created_at: str | None = None

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

# ===== REQUEST MODELS =====

class UserEmailRequest(BaseModel):
    """Request model for operations requiring user email"""
    email: str 