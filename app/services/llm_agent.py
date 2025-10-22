from typing import Annotated, List, Optional

import logfire
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.account import AccountResponse
from app.schemas.bank import BankResponse
from app.schemas.card import CardResponse
from app.schemas.transaction import TransactionQuery
from app.schemas.transaction import (
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawalRequest,
)
from app.schemas.user import UserResponse
from app.services.user_service import get_user_by_id
from app.services.account_service import (
    get_account_by_id,
    get_account_by_number,
    get_all_accounts,
)
from app.services.bank_service import get_all_active_banks
from app.services.card_service import get_user_cards
from app.services.transaction_service import (
    get_transactions,
    get_user_all_transactions,
    get_transaction_by_reference,
    deposit_funds,
    transfer_funds,
    withdraw_funds,
)


# ------------------------
# 🏦 Pydantic Models for Agent State
# ------------------------


class AgentDependencies(BaseModel):
    """Dependencies injected into the agent context"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    db: AsyncSession
    user_id: int


# ------------------------
# 🏦 Banking Agent Definition
# ------------------------

# Create the model once
_banking_model = OpenAIChatModel(
    model_name=settings.PYDANTIC_AI_MODEL,
    provider=DeepSeekProvider(api_key=settings.DEEPSEEK_API_KEY),
)

# Define the banking agent with all tools
banking_agent = Agent(
    model=_banking_model,
    system_prompt="""
    You are a helpful bank support assistant with REAL-TIME access to customer data. 
    You can access actual account information, transactions, and user profiles.

    CAPABILITIES:
    - View all user accounts and balances
    - Check specific account details
    - View recent transaction history
    - View user's payment cards (masked for security)
    - Access user profile information
    - Transfer funds between accounts
    - Deposit and withdraw funds
    - Look up transactions by reference
    - Get bank information
    - Get transactions for specific accounts

    SECURITY & GUIDELINES:
    - Only access data for the authenticated user
    - Never reveal full card numbers or sensitive details
    - Confirm important actions like transfers with the user
    - Be transparent about what data you're accessing
    - Use friendly, professional language
    - Provide clear, accurate financial information

    TOOL USAGE:
    - Use the appropriate tools based on user requests
    - For transfers, confirm details before executing
    - Provide helpful, personalized responses based on actual data
    """,
    deps_type=AgentDependencies,
)

# ------------------------
# 🛠️ Banking Tools with Proper Pydantic AI Patterns
# ------------------------


@banking_agent.tool
async def get_user_accounts(
    ctx: RunContext[AgentDependencies],
) -> List[AccountResponse]:
    """Get all accounts for the current user with balances and details."""
    try:
        accounts = await get_all_accounts(ctx.deps.db, ctx.deps.user_id)
        return [AccountResponse.model_validate(account) for account in accounts]
    except Exception as e:
        logfire.error("Error getting user accounts", error=str(e))
        return []


@banking_agent.tool
async def get_account_balance_details(
    ctx: RunContext[AgentDependencies], account_number: str
) -> Optional[AccountResponse]:
    """Get specific account details and balance by account number."""
    try:
        account = await get_account_by_number(ctx.deps.db, account_number)
        if account and account.user_id == ctx.deps.user_id:
            return AccountResponse.model_validate(account)
        return None
    except Exception as e:
        logfire.error("Error getting account balance", error=str(e))
        return None

@banking_agent.tool
async def get_user_payment_cards(
    ctx: RunContext[AgentDependencies],
) -> List[CardResponse]:
    """Get user's payment cards with masked numbers for security."""
    try:
        cards = await get_user_cards(ctx.deps.db, ctx.deps.user_id)
        return [CardResponse.model_validate(card) for card in cards]
    except Exception as e:
        logfire.error("Error getting user cards", error=str(e))
        return []


@banking_agent.tool
async def get_user_profile(
    ctx: RunContext[AgentDependencies],
) -> Optional[UserResponse]:
    """Get user profile information including name and contact details."""
    try:
        user = await get_user_by_id(ctx.deps.db, ctx.deps.user_id)
        if user:
            return UserResponse.model_validate(user)
        return None
    except Exception as e:
        logfire.error("Error getting user profile", error=str(e))
        return None
    

@banking_agent.tool
async def get_account_detail_by_id(
    ctx: RunContext[AgentDependencies], account_id: int
) -> Optional[AccountResponse]:
    """Get account details by account ID."""
    try:
        account = await get_account_by_id(ctx.deps.db, account_id)
        if account and account.user_id == ctx.deps.user_id:
            return AccountResponse.model_validate(account)
        return None
    except Exception as e:
        logfire.error("Error getting account by ID", error=str(e))
        return None


@banking_agent.tool
async def get_banks(ctx: RunContext[AgentDependencies]) -> List[BankResponse]:
    """Get list of all active banks in the system."""
    try:
        banks = await get_all_active_banks(ctx.deps.db)
        return [BankResponse.model_validate(bank) for bank in banks]
    except Exception as e:
        logfire.error("Error getting banks", error=str(e))
        return []


@banking_agent.tool
async def get_user_transactions_across_accounts(
    ctx: RunContext[AgentDependencies],
    limit: Annotated[int, "Number of transactions to return"] = 10,
) -> List[TransactionResponse]:
    """Get transactions for the user across all accounts."""
    try:
        if limit > 50:
            limit = 50
        
        # Use the renamed function
        transactions = await get_user_all_transactions(ctx.deps.db, ctx.deps.user_id, limit)
        return [TransactionResponse.model_validate(tx) for tx in transactions]
    except Exception as e:
        logfire.error("Error getting user transactions", error=str(e), stack_trace=True)
        return []

@banking_agent.tool
async def get_account_transactions(
    ctx: RunContext[AgentDependencies],
    account_number: str,
    limit: Annotated[int, "Number of transactions to return"] = 10,
) -> List[TransactionResponse]:
    """Get recent transactions for a specific account."""
    try:
        if limit > 50:
            limit = 50

        account = await get_account_by_number(ctx.deps.db, account_number)
        if not account or account.user_id != ctx.deps.user_id:
            return []

        # Use the correct get_transactions function with TransactionQuery
        query = TransactionQuery(account_id=account.id, limit=limit)
        transactions = await get_transactions(ctx.deps.db, query)
        
        return [TransactionResponse.model_validate(tx) for tx in transactions]
    except Exception as e:
        logfire.error("Error getting account transactions", error=str(e), stack_trace=True)
        return []


@banking_agent.tool
async def transfer_funds_between_accounts(
    ctx: RunContext[AgentDependencies], request: TransferRequest
) -> dict:
    """Transfer funds between two accounts."""
    try:
        transfer_data = TransferRequest.model_validate(
            {
                "from_account_number": request.from_account_number,
                "to_account_number": request.to_account_number,
                "amount": request.amount,
                "description": request.description,
            }
        )

        result = await transfer_funds(ctx.deps.db, transfer_data, ctx.deps.user_id)
        return {
            "success": True,
            "message": "Transfer completed successfully",
            "reference": getattr(result, "reference", "N/A"),
            "amount": request.amount,
            "from_account": request.from_account_number,
            "to_account": request.to_account_number,
        }
    except Exception as e:
        logfire.error("Error creating transfer", error=str(e))
        return {"error": str(e), "success": False}


@banking_agent.tool
async def deposit_funds_into_accounts(
    ctx: RunContext[AgentDependencies], request: DepositRequest
) -> dict:
    """Deposit funds into an account."""
    try:
        deposit_data = DepositRequest.model_validate(
            {
                "account_number": request.account_number,
                "amount": request.amount,
                "description": request.description,
            }
        )

        transaction = await deposit_funds(ctx.deps.db, deposit_data, ctx.deps.user_id)
        return {
            "success": True,
            "message": "Deposit successful",
            "reference": transaction.reference,
            "amount": request.amount,
            "account": request.account_number,
        }
    except Exception as e:
        logfire.error("Error depositing funds", error=str(e))
        return {"error": str(e), "success": False}


@banking_agent.tool
async def withdraw_funds_an_account(
    ctx: RunContext[AgentDependencies], request: WithdrawalRequest
) -> dict:
    """Withdraw funds from an account."""
    try:
        withdraw_data = WithdrawalRequest.model_validate(
            {
                "account_number": request.account_number,
                "amount": request.amount,
                "description": request.description,
            }
        )

        transaction = await withdraw_funds(ctx.deps.db, withdraw_data, ctx.deps.user_id)
        return {
            "success": True,
            "message": "Withdrawal successful",
            "reference": transaction.reference,
            "amount": request.amount,
            "account": request.account_number,
        }
    except Exception as e:
        logfire.error("Error withdrawing funds", error=str(e))
        return {"error": str(e), "success": False}



@banking_agent.tool
async def get_transaction_details_by_reference(
    ctx: RunContext[AgentDependencies], reference: str
) -> Optional[TransactionResponse]:
    """Get transaction details by reference number."""
    try:
        transaction = await get_transaction_by_reference(ctx.deps.db, reference)
        if transaction:
            account = await get_account_by_id(ctx.deps.db, transaction.account_id)
            if account and account.user_id == ctx.deps.user_id:
                return TransactionResponse.model_validate(transaction)
        return None
    except Exception as e:
        logfire.error("Error getting transaction by reference", error=str(e))
        return None

# ------------------------
# 🚀 Agent Functions
# ------------------------

async def chat_with_agent_enhanced(
    user_query: str, db: AsyncSession, user_id: int
) -> str:
    """Enhanced function to chat with banking agent using real data"""
    with logfire.span("enhanced_agent_chat", user_query=user_query, user_id=user_id):
        try:
            logfire.info("Calling enhanced banking agent...")

            # Create dependencies
            deps = AgentDependencies(db=db, user_id=user_id)

            # Run the agent with dependencies
            result = await banking_agent.run(user_query, deps=deps)

            # Simple approach - just return the string representation
            response_text = str(result)
            
            logfire.info(
                "Enhanced agent response successful",
                response_length=len(response_text)
            )
            return response_text

        except Exception as e:
            logfire.error(
                "Enhanced agent chat error", 
                error=str(e), 
                error_type=type(e).__name__,
                stack_trace=True
            )
            return f"I apologize, but I'm having trouble processing your request. Error: {str(e)}"