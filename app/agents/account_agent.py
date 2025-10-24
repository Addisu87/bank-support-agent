from dataclasses import dataclass

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from sqlalchemy import select

from app.core.config import settings
from app.core.session import get_user_db
from app.db.models.account import Account
from app.db.models.card import Card
from app.db.models.transaction import Transaction
from app.schemas.account import AccountInfo
from app.schemas.card import CardInfo
from app.schemas.transaction import TransactionInfo
from app.services.bank_service import list_banks

# ------------------------
# 🔧 Setup
# ------------------------
logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()


@dataclass
class AccountDependencies:
    email: str


account_model = OpenAIChatModel(
    model_name=settings.PYDANTIC_AI_MODEL,
    provider=DeepSeekProvider(api_key=settings.DEEPSEEK_API_KEY),
)

account_agent = Agent(
    account_model,
    deps_type=AccountDependencies,
    system_prompt=(
        "You are a helpful bank support agent. You can provide customer account balances and transactions. "
        "Always be polite and professional. When providing financial information, format numbers clearly "
        "and explain what the data means in a conversational way."
    ),
    instrument=True,
)

# ------------------------
# 🏦 Agent Tools
# ------------------------


@account_agent.tool
async def get_banks(ctx: RunContext[AccountDependencies]):
    """Returns a list of available banks."""
    banks = await list_banks()
    return banks if banks else "No banks found."


@account_agent.tool
async def get_customer_balance_by_email(ctx: RunContext[AccountDependencies]):
    """Returns all customer accounts and balances."""
    async with get_user_db(ctx.deps.email) as (db, user):
        if not user:
            return "User not found."

        result = await db.execute(select(Account).filter_by(user_id=user.id))
        accounts = result.scalars().all()
        if not accounts:
            return "No accounts found for this user."

        return [AccountInfo.model_validate(acc) for acc in accounts]


@account_agent.tool
async def recent_transactions(
    ctx: RunContext[AccountDependencies],
    account_number: str,
    limit: int = 5,
):
    """Returns the customer's recent transactions for a given account."""
    async with get_user_db(ctx.deps.email) as (db, user):
        if not user:
            return "User not found."

        account_result = await db.execute(
            select(Account.id).filter_by(user_id=user.id, account_number=account_number)
        )
        account_id = account_result.scalar_one_or_none()
        if not account_id:
            return f"Account {account_number} not found for this user."

        tx_result = await db.execute(
            select(Transaction)
            .filter_by(account_id=account_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
        transactions = tx_result.scalars().all()

        if not transactions:
            return f"No transactions found for account {account_number}."

        return [TransactionInfo.model_validate(tx) for tx in transactions]


@account_agent.tool
async def get_user_cards(ctx: RunContext[AccountDependencies]):
    """Returns the customer's cards with masked numbers."""
    async with get_user_db(ctx.deps.email) as (db, user):
        if not user:
            return "User not found."

        result = await db.execute(
            select(Card).join(Account).filter(Account.user_id == user.id)
        )
        cards = result.scalars().all()
        if not cards:
            return "No cards found for this user."

        return [CardInfo.model_validate(card) for card in cards]


@account_agent.tool
async def block_card(ctx: RunContext[AccountDependencies], card_number: str):
    """Block a customer's card for security purposes."""
    async with get_user_db(ctx.deps.email) as (db, user):
        if not user:
            return "User not found."

        result = await db.execute(
            select(Card)
            .join(Account)
            .filter(Card.card_number == card_number, Account.user_id == user.id)
        )
        card = result.scalar_one_or_none()
        if not card:
            return "Card not found."

        card.status = "blocked"
        await db.commit()
        return f"Card {card.card_number} has been blocked successfully."


@account_agent.tool
async def create_account(
    ctx: RunContext[AccountDependencies],
    bank_id: int,
    account_type: str = "checking",
    initial_balance: float = 0.0,
):
    """Create a new bank account for the customer."""
    async with get_user_db(ctx.deps.email) as (db, user):
        if not user:
            return "User not found."

        new_account = Account(
            user_id=user.id,
            bank_id=bank_id,
            account_type=account_type,
            balance=initial_balance,
            currency="USD",
        )
        db.add(new_account)
        await db.commit()
        await db.refresh(new_account)

        return AccountInfo.model_validate(new_account)
