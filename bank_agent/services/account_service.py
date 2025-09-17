"""
Shared account services to avoid code duplication between agent tools and MCP tools.
"""
import logfire
from typing import List, Dict, Optional
from bank_agent.db.crud import get_user_by_email, get_accounts_by_user, get_transactions, block_card_by_number as db_block_card_by_number, get_cards_by_user
from bank_agent.models.account import Transaction


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
