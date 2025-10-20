import logfire
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

from app.core.cache import cache
from app.core.config import settings

# ------------------------
# 🔧 Setup & Configuration
# ------------------------
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

# ------------------------
# 🏦 Simple Banking Agent
# ------------------------


def create_banking_agent() -> Agent:
    """Create a simple banking conversation agent"""
    model = OpenAIChatModel(
        model_name=settings.PYDANTIC_AI_MODEL,
        provider=DeepSeekProvider(api_key=settings.DEEPSEEK_API_KEY),
    )

    agent = Agent(
        model,
        system_prompt="""
        You are a helpful bank support assistant. Your role is to have conversational interactions 
        with users and provide helpful information about banking.

        You can help with:
        - Explaining banking concepts and features
        - Guiding users on how to use the banking app
        - Providing general financial tips
        - Answering questions about account management
        - Security best practices

        Important guidelines:
        - Be friendly, professional, and helpful
        - Guide users to use the actual banking app for transactions
        - Never ask for sensitive information (passwords, PINs, card numbers)
        - If you don't know something, admit it and suggest contacting support
        - Keep responses clear and conversational

        Remember: You're here to chat and guide, not to perform banking operations.
        """,
        instrument=True,
    )

    return agent


# Global agent instance
banking_agent = create_banking_agent()

# ------------------------
# 🏦 Simple Agent Functions
# ------------------------


async def chat_with_agent(user_query: str, use_cache: bool = True) -> str:
    """Simple function to chat with the banking agent"""
    with logfire.span("agent_chat", user_query=user_query):
        # Check cache first if enabled
        if use_cache:
            cache_key = f"agent_response:{hash(user_query)}"
            cached_response = await cache.get(cache_key)
            if cached_response:
                logfire.info("Returning cached agent response")
                return cached_response

        try:
            result = await banking_agent.run(user_query)
            response = result.data

            # Cache the response if enabled
            if use_cache:
                await cache.set(cache_key, response, expire=3600)  # 1 hour

            return response

        except Exception as e:
            logfire.error("Agent chat error", error=str(e))
            return "I apologize, but I'm having trouble responding right now. Please try again later or contact our support team for immediate assistance."


async def clear_agent_cache() -> int:
    """Clear all cached agent responses"""
    with logfire.span("clear_agent_cache"):
        pattern = "agent_response:*"
        keys = await cache.redis.keys(pattern)
        if keys:
            await cache.redis.delete(*keys)
            logfire.info(f"Cleared {len(keys)} cached responses")
        return len(keys)
