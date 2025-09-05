# Bank Support Agent following Pydantic AI patterns
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIChatModel
from bank_agent.models.agent_responses import SupportResponse
from bank_agent.db.storage import get_user_by_email
from bank_agent.core.config import settings
import asyncio

import logfire
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class SupportDependencies:
    user_email: str
    
# Legacy compatibility functions
class SupportQuery(BaseModel):
    user_id: str 
    message: str 

# Configure MCP servers for all agents
account_server = MCPServerStdio(  
    "npx", args=['bank_agent/agents/account_agent.py']
)

# card_server = MCPServerStdio(  
#      "npx", args=['bank_agent/agents/card_agent.py']
# )

# fraud_server = MCPServerStdio(  
#      "npx", args=['bank_agent/agents/fraud_agent.py']
# )

# media_server = MCPServerStdio(  
#      "npx", args=['bank_agent/agents/media_agent.py']
# )

# notification_server = MCPServerStdio(  
#      "npx", args=['bank_agent/agents/notification_agent.py']
# )

# Create the support agent
support_model = OpenAIChatModel(
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    toolsets=[account_server]
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
    instrument=True,
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    """Add customer full_name to system prompt."""
    try:
        # Get user by email from SQLAlchemy User model
        user = await get_user_by_email(ctx.deps.user_email)
        if user and user.full_name:
            return f"The customer's name is {user.full_name!r}"
    except Exception as e:
        return f"Error retrieving name: {str(e)}"
    return "The customer's name is not available"



async def main():
    async with support_agent:  
        deps = SupportDependencies(
            user_email="addisu@exampl.com"
        )
        result = await support_agent.run('How can resolve that I lost my card which has some money?', deps=deps)
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())