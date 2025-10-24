# tests/helpers.py
from fastapi.testclient import TestClient
import uuid


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
    print(f"Register user {email}: {response.status_code} - {response.text}")
    return response


def login_user(client: TestClient, email: str, password: str) -> dict:
    """Login user and return response"""
    login_data = {
        "username": email,
        "password": password
    }
    
    response = client.post("/api/v1/auth/token", data=login_data)
    print(f"Login user {email}: {response.status_code} - {response.text}")
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


def create_user_account(client: TestClient, token: str, account_type: str = "checking", initial_deposit: float = 1000.0) -> dict:
    """Create a user bank account and return response"""
    account_data = {
        "account_type": account_type,
        "initial_deposit": initial_deposit,
        "account_name": f"{account_type.capitalize()} Account",
        "bank_id": 1,  # Assuming there's a default bank with ID 1
    }
    
    response = client.post(
        "/api/v1/accounts/",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Create user account: {response.status_code} - {response.text}")
    return response


def get_user_accounts(client: TestClient, token: str) -> dict:
    """Get user's bank accounts"""
    response = client.get(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Get user accounts: {response.status_code} - {response.text}")
    return response


def create_bank(client: TestClient, token: str, bank_data: dict = None) -> dict:
    """Create a bank (financial institution)"""
    if bank_data is None:
        bank_data = {
            "name": "Test Bank",
            "code": "TEST001",
            "country": "United States",
            "currency": "USD",
            "contact_email": "contact@testbank.com",
            "contact_phone": "+1234567890",
            "website": "https://testbank.com",
            "address": "123 Test Street, Test City"
        }
    
    response = client.post(
        "/api/v1/banks/",
        json=bank_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Create bank: {response.status_code} - {response.text}")
    return response


def get_banks(client: TestClient, token: str) -> dict:
    """Get all banks"""
    response = client.get(
        "/api/v1/banks/",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Get banks: {response.status_code} - {response.text}")
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
    print(f"Create transaction: {response.status_code} - {response.text}")
    return response


def get_transactions(client: TestClient, token: str, account_id: int = None) -> dict:
    """Get transactions"""
    url = "/api/v1/transactions/"
    if account_id:
        url = f"/api/v1/accounts/{account_id}/transactions/"
    
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Get transactions: {response.status_code} - {response.text}")
    return response


def create_card(client: TestClient, token: str, account_id: int, card_data: dict = None) -> dict:
    """Create a card"""
    if card_data is None:
        card_data = {
            "account_id": account_id,
            "bank_id": 1,
            "card_number": "4111111111111111",
            "card_holder_name": "Test User",
            "card_type": "debit",
            "expiry_date": "2026-12-31",
            "cvv": "123"
        }
    
    response = client.post(
        "/api/v1/cards/",
        json=card_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Create card: {response.status_code} - {response.text}")
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
    print(f"Get cards: {response.status_code} - {response.text}")
    return response