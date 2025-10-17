"""
Chat and AI agent related models
"""
from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    """Request model for agent chat"""
    model_config = ConfigDict(from_attributes=True)
    
    email: str
    message: str

class ChatResponse(BaseModel):
    """Agent chat response"""
    response: str
