# User model + Pydantic schema
from pydantic import BaseModel, ConfigDict

class UserRegister(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    email: str 
    
class UserIn(UserRegister):
    hashed_password: str

class UserLogin(BaseModel):
    email: str 
    password: str 