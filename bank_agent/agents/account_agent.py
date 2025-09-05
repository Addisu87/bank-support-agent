from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from ..db.storage import save_audit, get_user_by_email
from bank_agent.core.config import settings
import asyncio  
import logfire

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class AccountDependencies:
    user_email: str

account_model = OpenAIChatModel(
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.DEEPSEEK_API_KEY   
                )

account_agent = Agent(
    account_model,
    deps_type=AccountDependencies,
    system_prompt=(
        'You are an account agent. You can fetch customer account balances.'
    ),
    instrument=True,
)

@account_agent.tool
async def get_customer_balance(
    ctx: RunContext[AccountDependencies], include_pending: bool = False
) -> str:
    """Returns the customer's current account balance."""
    logfire.info(f"Fetching balance for user: {ctx.deps.user_email}")
    
    try:
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

async def main():
    async with account_agent:  
        deps = AccountDependencies(
            user_email="addisu@exampl.com"
        )
        result = await account_agent.run('How can resolve that I lost my card which has some money?', deps=deps)
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())