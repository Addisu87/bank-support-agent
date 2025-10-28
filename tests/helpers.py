import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

def generate_unique_email():
    """Generate a unique email for each call"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


async def register_user(client: AsyncClient, email: str = None, password: str = "testpassword123") -> dict:
    """Register a new user and return response"""
    if email is None:
        email = generate_unique_email()
    
    user_data = {
        "email": email,
        "password": password,
        "full_name": "Test User",
        "phone_number": "+1234567890",
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    return response

async def login_user(client: AsyncClient, email: str, password: str) -> dict:
    """Login user and return response"""
    login_data = {
        "username": email,
        "password": password
    }
    
    response = await client.post("/api/v1/auth/token", data=login_data)
    return response


async def get_auth_token(client: AsyncClient, email: str = None) -> str:
    """Login user, return auth token"""
    if email is None:
        email = generate_unique_email()
    
    # Register user first
    await register_user(client, email, "testpassword123")
    
    # Login user
    login_response = await login_user(client, email, "testpassword123")
    if login_response.status_code != 200:
        raise Exception(f"Failed to login user {email}: {login_response.text}")
    
    token_data = login_response.json()
    return token_data["access_token"]


async def create_bank(client: AsyncClient, token: str, bank_data: dict = None) -> dict:
    """Create a bank (financial institution)"""
    if bank_data is None:
        bank_data = {
            "name": f"Test Bank {uuid.uuid4().hex[:8]}",
            "code": f"TB{uuid.uuid4().hex[:8]}",  # Always unique
            "country": "United States",
            "currency": "USD",
        }
    
    response = await client.post(
        "/api/v1/banks/",
        json=bank_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

async def get_banks(client: AsyncClient, token: str) -> dict:
    """Get all banks"""
    response = await client.get(
        "/api/v1/banks/",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


async def create_user_account(client: AsyncClient, token: str, account_type: str = "checking") -> dict:
    """Create a user bank account and return response"""
    # Get bank ID first
    banks_response = await client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
    banks_data = banks_response.json()
    banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    
    if not banks_list:
        # If no banks exist, create one first
        await create_bank(client, token)
        banks_response = await client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
        banks_data = banks_response.json()
        banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    
    bank_id = banks_list[0].get('id')
    
    account_data = {
        "account_type": account_type,
        "bank_id": bank_id,
    }
    
    response = await client.post(
        "/api/v1/accounts/",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

async def get_user_accounts(client: AsyncClient, token: str) -> dict:
    """Get user's bank accounts"""
    response = await client.get(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


async def create_transaction(client: AsyncClient, token: str, account_id: int, transaction_data: dict = None) -> dict:
    """Create a transaction"""
    if transaction_data is None:
        transaction_data = {
            "account_id": account_id,
            "amount": 100.0,
            "transaction_type": "deposit",
            "description": "Test deposit transaction"
        }
    
    response = await client.post(
        "/api/v1/transactions/",
        json=transaction_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


async def get_transactions(client: AsyncClient, token: str, account_id: int = None) -> dict:
    """Get transactions"""
    url = "/api/v1/transactions/"
    if account_id:
        url = f"/api/v1/transactions/?account_id={account_id}"
    
    response = await client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


async def create_card(client: AsyncClient, token: str, account_id: int, card_data: dict = None) -> dict:
    """Create a card"""
    if card_data is None:
        card_data = {
            "card_holder_name": "TEST USER",
            "card_type": "debit",
        }
    
    response = await client.post(
        f"/api/v1/cards/{account_id}",
        json=card_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

async def get_cards(client: AsyncClient, token: str, account_id: int = None) -> dict:
    """Get cards"""
    url = "/api/v1/cards/"
    if account_id:
        url = f"/api/v1/accounts/{account_id}/cards/"
    
    response = await client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


# Mock the LLM agent to avoid API calls during testing
@pytest.fixture(autouse=True)
def mock_llm_dependencies():
    """Mock LLM dependencies for all tests"""
    with patch('app.services.llm_agent.DeepSeekProvider') as mock_provider:
        with patch('app.services.llm_agent.Agent') as mock_agent:
            # Configure the mock provider
            mock_provider_instance = MagicMock()
            mock_provider.return_value = mock_provider_instance
            
            # Configure the mock agent
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance
            
            # Mock the chat method to return a predictable response
            mock_agent_instance.run.return_value = MagicMock(
                answer="This is a mock response for testing purposes."
            )
            
            yield