from pydantic import BaseModel, ConfigDict

class CardQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    action: str
    card_id: str
    
class CardResponse(BaseModel):
    success: bool
    message: str
