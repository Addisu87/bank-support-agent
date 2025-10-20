from fastapi import APIRouter, Depends
from app.services.llm_agent import chat_with_agent, clear_agent_cache
from app.db.models.user import User
from app.core.deps import get_current_active_user
from app.schemas.agent import ChatRequest, ChatResponse

router = APIRouter(tags=["ai-agent"])

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Simple chat endpoint with the banking assistant"""
    response = await chat_with_agent(request.message, request.use_cache)
    return ChatResponse(response=response)

@router.post("/clear-cache")
async def clear_cache(current_user: User = Depends(get_current_active_user)):
    """Clear agent cache (admin only)"""
    if not current_user.is_superuser:
        return {"error": "Not authorized"}
    
    cleared = await clear_agent_cache()
    return {"message": f"Cleared {cleared} cached responses"}