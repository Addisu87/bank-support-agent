# Bank Support Agent following Pydantic AI patterns
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from ..db.storage import save_audit, get_user_by_email, create_user
from ..models.agent_responses import SupportResponse
from bank_agent.core.config import settings


@dataclass
class SupportDependencies:
    user_email: str
    
# Legacy compatibility functions
class SupportQuery(BaseModel):
    user_id: str 
    message: str 

# Create the support agent
support_model = OpenAIChatModel(
   model_name=settings.OPENAI_MODEL,
)

support_agent = Agent(
    support_model,
    deps_type=SupportDependencies,
    output_type=SupportResponse,
    system_prompt=(
        'You are a support agent in our bank. Give the customer support '
        'and judge the risk level of their query. Reply using the customer\'s name '
        'when available. Be helpful, secure, and professional.'
    ),
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    """Add customer name to system prompt."""
    try:
        # Get user by email from SQLAlchemy User model
        user = await get_user_by_email(ctx.deps.user_email)
        if user and user.name:
            return f"The customer's name is {user.name!r}"
    except:
        pass
    return "The customer's name is not available"


@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool = False
) -> str:
    """Returns the customer's current account balance."""
    try:
        # Get user by email
        user = await get_user_by_email(ctx.deps.user_email)
        if not user:
            return "User not found"
        
        # Mock balance implementation - in real app, this would query actual balance
        # Using user ID for balance logic
        if user.id == 1:  # First user gets higher balance
            balance = 123.45 if include_pending else 100.00
        else:
            balance = 50.00  # Default balance for other users
        
        # Log the balance inquiry
        await save_audit(
            actor=ctx.deps.user_email,
            tool="balance.inquiry",
            args=f"include_pending={include_pending}",
            result=f"balance={balance}"
        )
        
        return f'${balance:.2f}'
    except Exception as e:
        return f"Error retrieving balance: {str(e)}"


@support_agent.tool
async def block_customer_card(ctx: RunContext[SupportDependencies]) -> str:
    """Block the customer's card for security."""
    try:
        # Get user by email
        user = await get_user_by_email(ctx.deps.user_email)
        if not user:
            return "User not found"
        
        # Log the card blocking action
        await save_audit(
            actor=ctx.deps.user_email,
            tool="card.block",
            args=f"user_email={ctx.deps.user_email}",
            result="card_blocked"
        )
        return "Card has been blocked successfully"
    except Exception as e:
        return f"Error blocking card: {str(e)}"