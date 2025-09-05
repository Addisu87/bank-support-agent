from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from bank_agent.core.config import settings
import asyncio
import logfire


logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class NotificationDependencies:
    user_email: str

notification_model = OpenAIChatModel(   
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.DEEPSEEK_API_KEY
                )

notification_agent = Agent(
    notification_model,
    deps_type=NotificationDependencies,
    system_prompt=(
        'You are a notification agent. You can send notifications to users.'
    ),
    instrument=True,
)

@notification_agent.tool
async def send_notification(ctx: RunContext[NotificationDependencies], message: str, recipient_email: str) -> str:
    """Sends a notification to a specified email address."""
    logfire.info(f"Sending notification to {recipient_email} from {ctx.deps.user_email}: {message}")
    # In a real application, this would send an email or push notification
    return f"Notification sent to {recipient_email}."

async def main():
    async with notification_agent:  
        deps = NotificationDependencies(
            user_email="addisu@exampl.com"
        )
        result = await notification_agent.run('How can resolve that I lost my card which has some money?', deps=deps)
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())