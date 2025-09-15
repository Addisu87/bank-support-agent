"""
Shared account services to avoid code duplication between agent tools and MCP tools.
"""
import logfire
from typing import List, Dict, Optional
from bank_agent.db.crud import get_user_by_email, get_accounts_by_user, get_transactions
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
