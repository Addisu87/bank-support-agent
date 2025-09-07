from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from ..db.crud import get_user_by_email, get_accounts_by_user, get_transactions
from bank_agent.core.config import settings
from pydantic_ai.mcp import MCPServerStdio
import logfire
    
from bank_agent.models.account import Transaction

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()


server = MCPServerStdio(  
    'uv', args=['run', 'mcp-run-python', 'stdio'], timeout=10
)

@dataclass
class AccountDependencies:
    user_email: str  

account_model = OpenAIChatModel(
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    toolsets=[server]  
                )

account_agent = Agent(
    account_model,
    deps_type=AccountDependencies,
    system_prompt=(
        'You are an account agent. You can provide customer account balances and transactions'
    ),
    instrument=True,
)

@account_agent.tool
async def get_customer_balance_by_email(ctx: RunContext[AccountDependencies]):
    """Returns the customer's current account balance."""
    logfire.info(f"Fetching balance for user: {ctx.deps.user_email}")

    user = await get_user_by_email(ctx.deps.user_email)
    if not user:
        return "User not found"
    
    accounts = await get_accounts_by_user(user.id)
    return [{
            "account_number": acc.account_number, 
            "balance": acc.balance, 
            "currency": acc.currency
            }
        for acc in accounts]

@account_agent.tool
async def recent_transactions(ctx: RunContext[AccountDependencies], account_number: str, limit: int = 5):
    """Returns the customer's recent transactions for a given account."""
    logfire.info(f"Fetching recent transactions for user: {ctx.deps.user_email}, account: {account_number}")

    user = await get_user_by_email(ctx.deps.user_email)
    if not user:
        return "User not found"
    
    accounts = await get_accounts_by_user(user.id)
    account = next((acc for acc in accounts if acc.account_number == account_number), None)
    
    if not account:
        return f"Account with number {account_number} not found for this user."
        
    transactions = await get_transactions(account.id, limit)
    return [Transaction.model_validate(tx).model_dump() for tx in transactions]
    