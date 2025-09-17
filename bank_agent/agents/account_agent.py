from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from bank_agent.core.config import settings
from bank_agent.services.account_service import get_customer_accounts_data, get_account_transactions_data, block_card_by_number, get_user_cards_data, get_banking_demo_info, create_new_account
import logfire

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class AccountDependencies:
    user_email: str  

account_model = OpenAIChatModel(
    model_name=settings.PYDANTIC_AI_MODEL,
    provider=DeepSeekProvider(api_key=settings.DEEPSEEK_API_KEY)
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

@account_agent.tool
async def get_user_cards(ctx: RunContext[AccountDependencies]):
    """Returns the customer's cards with masked numbers."""
    cards = await get_user_cards_data(ctx.deps.user_email)
    return cards if cards else "No cards found for this user"

@account_agent.tool
async def block_card(ctx: RunContext[AccountDependencies], card_number: str):
    """Block a customer's card for security purposes."""
    result = await block_card_by_number(ctx.deps.user_email, card_number)
    return result

@account_agent.tool
async def get_banking_info(ctx: RunContext[AccountDependencies]):
    """Get information about available banking services and demo data from real banks."""
    result = await get_banking_demo_info()
    return result

@account_agent.tool
async def create_account(ctx: RunContext[AccountDependencies], account_type: str = "checking", initial_balance: float = 0.0):
    """Create a new bank account for the customer."""
    result = await create_new_account(ctx.deps.user_email, account_type, initial_balance)
    return result
