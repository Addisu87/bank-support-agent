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
class CardDependencies:
    user_email: str

card_model = OpenAIChatModel(
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.DEEPSEEK_API_KEY
                )

card_agent = Agent(
    card_model,
    deps_type=CardDependencies,
    system_prompt=(
        'You are a card agent. You can block customer cards.'
    ),
    instrument=True,
)

@card_agent.tool
async def block_customer_card(ctx: RunContext[CardDependencies]) -> str:
    """Block the customer's card for security."""
    logfire.info(f"Blocking card for user: {ctx.deps.user_email}")
    
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

async def main():
    async with card_agent:  
        deps = CardDependencies(
            user_email="addisu@exampl.com"
        )
        result = await card_agent.run('How can resolve that I lost my card which has some money?', deps=deps)
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())