"""
Shared account services to avoid code duplication between agent tools and MCP tools.
"""
import logfire
from typing import List, Dict, Optional
from bank_agent.db.crud import get_user_by_email, get_accounts_by_user, get_transactions, block_card_by_number as db_block_card_by_number, get_cards_by_user, create_account, create_bank
from sqlalchemy import select
from bank_agent.db.models import Bank
from bank_agent.db.postgres import AsyncSessionLocal
from bank_agent.models.transaction import Transaction
from bank_agent.services.obp_service import obp_service


async def get_customer_accounts_data(user_email: str) -> List[Dict]:
    """
    Get customer account balances by email.
    
    Args:
        user_email: The email of the user to fetch accounts for
        
    Returns:
        List of account dictionaries with account_number, balance, and currency
        Empty list if user not found
    """
    logfire.info(f"Fetching balance for user: {user_email}")

    user = await get_user_by_email(user_email)
    if not user:
        logfire.warning(f"User not found: {user_email}")
        return []
    
    accounts = await get_accounts_by_user(user.id)
    return [{
        "account_number": acc.account_number, 
        "balance": acc.balance, 
        "currency": acc.currency
    } for acc in accounts]


async def get_account_transactions_data(user_email: str, account_number: str, limit: int = 5) -> List[Dict]:
    """
    Get recent transactions for a specific account.
    
    Args:
        user_email: The email of the user
        account_number: The account number to get transactions for
        limit: Maximum number of transactions to return
        
    Returns:
        List of transaction dictionaries
        Empty list if user or account not found
    """
    logfire.info(f"Fetching recent transactions for user: {user_email}, account: {account_number}")

    user = await get_user_by_email(user_email)
    if not user:
        logfire.warning(f"User not found: {user_email}")
        return []
    
    accounts = await get_accounts_by_user(user.id)
    account = next((acc for acc in accounts if acc.account_number == account_number), None)
    
    if not account:
        logfire.warning(f"Account {account_number} not found for user {user_email}")
        return []
        
    transactions = await get_transactions(account.id, limit)
    return [Transaction.model_validate(tx).model_dump() for tx in transactions]


async def get_user_cards_data(user_email: str) -> List[Dict]:
    """
    Get all cards for a user.
    
    Args:
        user_email: The email of the user to fetch cards for
        
    Returns:
        List of card dictionaries with masked card numbers
        Empty list if user not found
    """
    logfire.info(f"Fetching cards for user: {user_email}")

    user = await get_user_by_email(user_email)
    if not user:
        logfire.warning(f"User not found: {user_email}")
        return []
    
    cards = await get_cards_by_user(user.id)
    return [{
        "card_id": card.id,
        "card_number": f"****-****-****-{card.card_number[-4:]}",
        "card_type": card.card_type,
        "status": card.status,
        "expiry_date": card.expiry_date.isoformat() if card.expiry_date else None
    } for card in cards]


async def block_card_by_number(user_email: str, card_number: str) -> Dict:
    """
    Block a card by card number for security purposes.
    
    Args:
        user_email: The email of the user
        card_number: The card number to block
        
    Returns:
        Dictionary with status and message
    """
    logfire.info(f"Blocking card for user: {user_email}, card: {card_number}")

    user = await get_user_by_email(user_email)
    if not user:
        logfire.warning(f"User not found: {user_email}")
        return {"status": "error", "message": "User not found"}
    
    # Block the card in the database
    result = await db_block_card_by_number(card_number, user.id)
    
    if not result:
        logfire.warning(f"Card {card_number} not found for user {user_email}")
        return {
            "status": "error", 
            "message": f"Card ending in {card_number[-4:]} not found or does not belong to you."
        }
    
    if result["already_blocked"]:
        logfire.info(f"Card {card_number} was already blocked for user {user_email}")
        return {
            "status": "info",
            "message": f"Card ending in {card_number[-4:]} was already blocked.",
            "card_number": f"****-****-****-{card_number[-4:]}",
            "card_status": "blocked"
        }
    
    # Card was successfully blocked
    card = result["card"]
    logfire.info(f"Successfully blocked card {card_number} for user {user_email}")
    
    return {
        "status": "success", 
        "message": f"Card ending in {card_number[-4:]} has been blocked for security. Please contact customer service for a replacement.",
        "card_number": f"****-****-****-{card_number[-4:]}",
        "card_type": card.card_type,
        "card_status": card.status,
        "blocked_at": card.created_at.isoformat() if card.created_at else None
    }


async def get_banking_demo_info() -> Dict:
    """
    Get demo banking information from OBP sandbox.
    
    Returns:
        Dictionary with demo banking information
    """
    logfire.info("Fetching demo banking information from OBP")
    return await obp_service.get_demo_banking_scenario()


async def get_or_create_default_bank() -> Dict:
    """
    Get an existing bank or create a default one.
    
    Returns:
        Dictionary with bank information or error
    """
    try:
        # Try to find an existing bank first
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Bank).limit(1))
            existing_bank = result.scalar_one_or_none()
        
        if existing_bank:
            logfire.info(f"Using existing bank: {existing_bank.name}")
            return {
                "status": "success",
                "bank": existing_bank,
                "message": f"Using existing bank: {existing_bank.name}"
            }
        else:
            # Create a default bank if none exists
            bank = await create_bank(name="Demo Bank", bic="DEMO123", country="US")
            logfire.info(f"Created new bank: {bank.name}")
            return {
                "status": "success", 
                "bank": bank,
                "message": f"Created new bank: {bank.name}"
            }
            
    except Exception as e:
        logfire.error(f"Error managing bank: {str(e)}")
        return {
            "status": "error",
            "bank": None,
            "message": f"Failed to get or create bank: {str(e)}"
        }


async def create_new_account(user_email: str, account_type: str = "checking", initial_balance: float = 0.0) -> Dict:
    """
    Create a new bank account for a user.
    
    Args:
        user_email: The email of the user
        account_type: Type of account (checking, savings, etc.)
        initial_balance: Starting balance for the account
        
    Returns:
        Dictionary with account creation result
    """
    logfire.info(f"Creating new {account_type} account for user: {user_email}")

    user = await get_user_by_email(user_email)
    if not user:
        logfire.warning(f"User not found: {user_email}")
        return {"status": "error", "message": "User not found"}
    
    # Get or create a bank first
    bank_result = await get_or_create_default_bank()
    if bank_result["status"] != "success":
        return bank_result
    
    bank = bank_result["bank"]
    
    try:
        # Create the account
        account = await create_account(
            user_id=user.id,
            bank_id=bank.id,
            account_type=account_type,
            balance=initial_balance,
            currency="USD"
        )
        
        logfire.info(f"Successfully created account {account.account_number} for user {user_email}")
        
        return {
            "status": "success",
            "message": f"Successfully created {account_type} account",
            "account_number": account.account_number,
            "account_type": account.account_type,
            "balance": account.balance,
            "currency": account.currency,
            "created_at": account.created_at.isoformat() if account.created_at else None
        }
        
    except Exception as e:
        logfire.error(f"Error creating account: {str(e)}")
        return {"status": "error", "message": f"Failed to create account: {str(e)}"}
