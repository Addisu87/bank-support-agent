from fastapi import APIRouter, Depends

from app.core.deps import get_current_active_user
from app.db.models.user import User
from app.schemas.agent import ChatRequest, ChatResponse
from app.services.llm_agent import chat_with_agent

router = APIRouter(tags=["ai-agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, current_user: User = Depends(get_current_active_user)
):
    """Simple chat endpoint with the banking assistant"""
    response = await chat_with_agent(request.message)
    return ChatResponse(response=response)
