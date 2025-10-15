from pydantic import BaseModel, ConfigDict

class CardQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    action: str
    card_id: str
    
class CardResponse(BaseModel):
    success: bool
    message: str

# ===== API MODELS =====

class BlockCardRequest(BaseModel):
    """Request model for blocking cards"""
    email: str
    card_number: str

class CardBlockResponse(BaseModel):
    """Response for card blocking operations"""
    status: str
    message: str
    card_number: str | None = None  # Masked
    card_type: str | None = None
    card_status: str | None = None
    blocked_at: str | None = None

class CardInfo(BaseModel):
    """Card information model for API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    card_id: int | None = None
    card_number: str  # Masked format
    card_type: str
    status: str
    expiry_date: str | None = None
