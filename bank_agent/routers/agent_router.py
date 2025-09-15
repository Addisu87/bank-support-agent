from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bank_agent.agents.account_agent import account_agent, AccountDependencies

router = APIRouter()

class ChatRequest(BaseModel):
    user_email: str
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the bank support agent.
    The agent can help with account balances and transaction history.
    """
    try:
        # Create dependencies with user email
        deps = AccountDependencies(user_email=request.user_email)
        
        # Run the agent with the user's message
        result = await account_agent.run(request.message, deps=deps)
        
        return ChatResponse(response=result.output)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/health")
async def agent_health():
    """Health check for the agent router."""
    return {"status": "Agent is ready"}
