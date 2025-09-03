# User model + Pydantic schema
from pydantic import BaseModel, ConfigDict

class UserRegister(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int | None = None
    name: str
    email: str 
    
class UserIn(UserRegister):
    password: str 

class UserLogin(BaseModel):
    email: str 
    password: str 