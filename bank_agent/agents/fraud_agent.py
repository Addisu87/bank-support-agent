from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from bank_agent.core.config import settings
import asyncio
import logfire

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class FraudDependencies:
    user_email: str

fraud_model = OpenAIChatModel( 
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.DEEPSEEK_API_KEY
                    )

fraud_agent = Agent(
    fraud_model,
    deps_type=FraudDependencies,
    system_prompt=(
        'You are a fraud agent. You can report fraudulent activities.'
    ),
    instrument=True,
)

@fraud_agent.tool
async def report_fraud(ctx: RunContext[FraudDependencies], transaction_id: str) -> str:
    """Reports a fraudulent transaction."""
    logfire.info(f"Reporting fraud for user: {ctx.deps.user_email}, transaction: {transaction_id}")
    # In a real application, this would interact with a fraud detection system
    return f"Fraud reported for transaction {transaction_id}."

async def main():
    async with fraud_agent:  
        deps = FraudDependencies(
            user_email="addisu@exampl.com"
        )
        result = await fraud_agent.run('How can resolve that I lost my card which has some money?', deps=deps)
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())