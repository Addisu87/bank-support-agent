from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from bank_agent.core.config import settings
from bank_agent.services.account_service import get_customer_accounts_data, get_account_transactions_data
import logfire

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class AccountDependencies:
    user_email: str  

# Create OpenAI provider with your API key
openai_provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)

account_model = OpenAIChatModel(
    model_name=settings.PYDANTIC_AI_MODEL,
    provider=openai_provider
)

account_agent = Agent(
    account_model,
    deps_type=AccountDependencies,
    system_prompt=(
        'You are a helpful bank support agent. You can provide customer account balances and transactions. '
        'Always be polite and professional. When providing financial information, format numbers clearly '
        'and explain what the data means in a conversational way.'
    ),
    instrument=True,
)

@account_agent.tool
async def get_customer_balance_by_email(ctx: RunContext[AccountDependencies]):
    """Returns the customer's current account balance."""
    accounts = await get_customer_accounts_data(ctx.deps.user_email)
    return accounts if accounts else "User not found"

@account_agent.tool
async def recent_transactions(ctx: RunContext[AccountDependencies], account_number: str, limit: int = 5):
    """Returns the customer's recent transactions for a given account."""
    transactions = await get_account_transactions_data(ctx.deps.user_email, account_number, limit)
    if not transactions:
        return f"No transactions found for account {account_number} or user not found."
    return transactions
