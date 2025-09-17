from fastapi import APIRouter
from bank_agent.services.account_service import get_customer_accounts_data, get_account_transactions_data, block_card_by_number, get_user_cards_data, get_banking_demo_info, create_new_account, get_or_create_default_bank
from bank_agent.models.user import UserEmailRequest
from bank_agent.models.account import CreateAccountRequest, AccountCreationResponse
from bank_agent.models.transaction import TransactionRequest
from bank_agent.models.card import BlockCardRequest, CardBlockResponse
from bank_agent.models.bank import BankingInfoResponse

# Create FastAPI router for banking operations
router = APIRouter()

# FastAPI endpoints (visible in /docs)
@router.post("/balance")
async def get_customer_balance(request: UserEmailRequest):
    """Get customer account balances by email address."""
    return await get_customer_accounts_data(request.user_email)

@router.post("/transactions")
async def get_recent_transactions(request: TransactionRequest):
    """Get recent transactions for a specific account."""
    return await get_account_transactions_data(request.user_email, request.account_number, request.limit)

@router.post("/cards")
async def get_cards(request: UserEmailRequest):
    """Get customer's cards with masked numbers."""
    return await get_user_cards_data(request.user_email)

@router.post("/block-card")
async def block_customer_card(request: BlockCardRequest):
    """Block a customer's card for security purposes."""
    return await block_card_by_number(request.user_email, request.card_number)

@router.post("/create-account")
async def create_bank_account(request: CreateAccountRequest):
    """Create a new bank account for a customer."""
    return await create_new_account(request.user_email, request.account_type, request.initial_balance)

@router.get("/banking-info")
async def get_banking_information():
    """Get information about available banking services and connected banks."""
    return await get_banking_demo_info()

@router.get("/default-bank")
async def get_bank_info():
    """Get or create the default bank for account creation."""
    return await get_or_create_default_bank()
