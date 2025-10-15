"""
Chat and AI agent related models
"""
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Request model for agent chat"""
    email: str
    message: str

class ChatResponse(BaseModel):
    """Agent chat response"""
    response: str
