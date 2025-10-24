import uuid

from fastapi.testclient import TestClient


def generate_unique_email():
    """Generate a unique email for each call"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, email: str = None, password: str = "testpassword123") -> dict:
    """Register a new user and return response"""
    if email is None:
        email = generate_unique_email()
    
    user_data = {
        "email": email,
        "password": password,
        "full_name": "Test User",
        "phone_number": "+1234567890",
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    return response

def login_user(client: TestClient, email: str, password: str) -> dict:
    """Login user and return response"""
    login_data = {
        "username": email,
        "password": password
    }
    
    response = client.post("/api/v1/auth/token", data=login_data)
    return response


def get_auth_token(client: TestClient, email: str = None) -> str:
    """Login user, return auth token"""
    if email is None:
        email = generate_unique_email()
    
    # Register user first
    register_response = register_user(client, email, "testpassword123")
    
    # Login user
    login_response = login_user(client, email, "testpassword123")
    if login_response.status_code != 200:
        raise Exception(f"Failed to login user {email}: {login_response.text}")
    
    token_data = login_response.json()
    return token_data["access_token"]


def create_bank(client: TestClient, token: str, bank_data: dict = None) -> dict:
    """Create a bank (financial institution)"""
    if bank_data is None:
        bank_data = {
            "name": f"Test Bank {uuid.uuid4().hex[:8]}",
            "code": f"TB{uuid.uuid4().hex[:8]}",  # Always unique
            "country": "United States",
            "currency": "USD",
        }
    
    response = client.post(
        "/api/v1/banks/",
        json=bank_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_banks(client: TestClient, token: str) -> dict:
    """Get all banks"""
    response = client.get(
        "/api/v1/banks/",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


def create_user_account(client: TestClient, token: str, account_type: str = "checking") -> dict:
    """Create a user bank account and return response"""
    # Get bank ID first
    banks_response = client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
    banks_data = banks_response.json()
    banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    
    if not banks_list:
        # If no banks exist, create one first
        create_bank(client, token)
        banks_response = client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
        banks_data = banks_response.json()
        banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    
    bank_id = banks_list[0].get('id')
    
    account_data = {
        "account_type": account_type,
        "bank_id": bank_id,
    }
    
    response = client.post(
        "/api/v1/accounts/",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_user_accounts(client: TestClient, token: str) -> dict:
    """Get user's bank accounts"""
    response = client.get(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


def create_transaction(client: TestClient, token: str, account_id: int, transaction_data: dict = None) -> dict:
    """Create a transaction"""
    if transaction_data is None:
        transaction_data = {
            "account_id": account_id,
            "amount": 100.0,
            "transaction_type": "deposit",
            "description": "Test deposit transaction"
        }
    
    response = client.post(
        "/api/v1/transactions/",
        json=transaction_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


def get_transactions(client: TestClient, token: str, account_id: int = None) -> dict:
    """Get transactions"""
    url = "/api/v1/transactions/"
    if account_id:
        url = f"/api/v1/transactions/?account_id={account_id}"
    
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response


def create_card(client: TestClient, token: str, account_id: int, card_data: dict = None) -> dict:
    """Create a card"""
    if card_data is None:
        card_data = {
            "card_holder_name": "TEST USER",
            "card_type": "debit",
        }
    
    response = client.post(
        f"/api/v1/cards/{account_id}",
        json=card_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_cards(client: TestClient, token: str, account_id: int = None) -> dict:
    """Get cards"""
    url = "/api/v1/cards/"
    if account_id:
        url = f"/api/v1/accounts/{account_id}/cards/"
    
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response