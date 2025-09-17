from fastapi import APIRouter, HTTPException
from bank_agent.agents.account_agent import account_agent, AccountDependencies
from bank_agent.services.account_service import create_new_account
from bank_agent.models.chat import ChatRequest, ChatResponse
from bank_agent.models.account import CreateAccountRequest, AccountCreationResponse

router = APIRouter()

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

@router.post("/create-account", response_model=AccountCreationResponse)
async def create_account_endpoint(request: CreateAccountRequest):
    """
    Create a new bank account for a user.
    """
    try:
        result = await create_new_account(
            user_email=request.user_email,
            account_type=request.account_type,
            initial_balance=request.initial_balance
        )
        
        return AccountCreationResponse(
            status=result["status"],
            message=result["message"],
            account_number=result.get("account_number"),
            account_type=result.get("account_type"),
            balance=result.get("balance"),
            currency=result.get("currency"),
            created_at=result.get("created_at")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")

@router.get("/health")
async def agent_health():
    """Health check for the agent router."""
    return {"status": "Agent is ready"}
