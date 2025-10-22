from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.schemas.agent import ChatRequest, ChatResponse
from app.services.llm_agent import chat_with_agent_enhanced

router = APIRouter(tags=["ai-agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Enhanced chat endpoint with real account data access"""
    try:
        response = await chat_with_agent_enhanced(request.message, db, current_user.id)
        return ChatResponse(response=response)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process your request at this time. Please try again later.",
        )
