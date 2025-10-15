import logfire
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from app.core.config import settings
from app.services.account_service import get_accounts_by_user, create_account as create_account_service, get_user_id_from_email, get_account_id_for_user
from app.services.transaction_service import get_transactions
from app.services.card_service import block_card_by_number, get_cards_by_user
from app.services.bank_service import list_banks

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class AccountDependencies:
    email: str  

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
async def get_banks(ctx: RunContext[AccountDependencies]):
    """Returns a list of available banks."""
    banks = await list_banks()
    return banks if banks else "No banks found."

@account_agent.tool
async def get_customer_balance_by_email(ctx: RunContext[AccountDependencies]):
    """Returns the customer's current account balance."""
    user_id = await get_user_id_from_email(ctx.deps.email)
    if not user_id:
        return "User not found."
    accounts = await get_accounts_by_user(user_id)
    return accounts if accounts else "No accounts found for this user."

@account_agent.tool
async def recent_transactions(ctx: RunContext[AccountDependencies], account_number: str, limit: int = 5):
    """Returns the customer's recent transactions for a given account."""
    user_id = await get_user_id_from_email(ctx.deps.email)
    if not user_id:
        return "User not found."
    account_id = await get_account_id_for_user(user_id, account_number)
    if not account_id:
        return f"Account {account_number} not found for this user."
    transactions = await get_transactions(account_id, limit)
    if not transactions:
        return f"No transactions found for account {account_number}."
    return transactions

@account_agent.tool
async def get_user_cards(ctx: RunContext[AccountDependencies]):
    """Returns the customer's cards with masked numbers."""
    user_id = await get_user_id_from_email(ctx.deps.email)
    if not user_id:
        return "User not found."
    cards = await get_cards_by_user(user_id)
    return cards if cards else "No cards found for this user"

@account_agent.tool
async def block_card(ctx: RunContext[AccountDependencies], card_number: str):
    """Block a customer's card for security purposes."""
    user_id = await get_user_id_from_email(ctx.deps.email)
    if not user_id:
        return "User not found."
    result = await block_card_by_number(card_number, user_id)
    return result

@account_agent.tool
async def create_account(ctx: RunContext[AccountDependencies], bank_id: int, account_type: str = "checking", initial_balance: float = 0.0):
    """Create a new bank account for the customer."""
    user_id = await get_user_id_from_email(ctx.deps.email)
    if not user_id:
        return "User not found."
    result = await create_account_service(user_id=user_id, bank_id=bank_id, account_type=account_type, balance=initial_balance)
    return result