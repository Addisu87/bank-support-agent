# tests/api/v1/test_accounts.py
import pytest
import uuid
from tests.helpers import (
    get_auth_token,
    create_user_account,
    get_user_accounts
)


def generate_unique_email():
    """Generate a unique email for each test run"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_create_user_account(client):
    """Test creating a user bank account"""
    # Get auth token using helper with unique email
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create user account
    response = create_user_account(client, token, "checking", 1000.0)
    
    # If 422, show detailed validation errors
    if response.status_code == 422:
        error_data = response.json()
        print("Detailed validation errors:")
        for error in error_data.get('detail', []):
            loc = error.get('loc', [])
            msg = error.get('msg')
            print(f"  - Field {loc}: {msg}")
        pytest.fail(f"User account creation failed with validation errors: {error_data}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["account_type"] == "checking"
    assert data["balance"] == 1000.0
    assert "id" in data
    assert "account_number" in data


def test_get_user_accounts(client):
    """Test getting user accounts"""
    # Get auth token using helper with unique email
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # First create an account to ensure there's something to get
    create_response = create_user_account(client, token, "checking", 500.0)
    
    if create_response.status_code == 201:
        # Get accounts
        response = get_user_accounts(client, token)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    else:
        pytest.skip("Account creation failed, skipping get accounts test")


def test_create_multiple_account_types(client):
    """Test creating multiple account types for a user"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create checking account
    checking_response = create_user_account(client, token, "checking", 500.0)
    assert checking_response.status_code == 201
    
    # Create savings account
    savings_response = create_user_account(client, token, "savings", 1500.0)
    assert savings_response.status_code == 201
    
    # Get all accounts
    accounts_response = get_user_accounts(client, token)
    assert accounts_response.status_code == 200
    accounts = accounts_response.json()
    assert isinstance(accounts, list)
    assert len(accounts) == 2


def test_account_balance_calculation(client):
    """Test that account balance is calculated correctly"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create account with initial deposit
    initial_deposit = 1000.0
    response = create_user_account(client, token, "checking", initial_deposit)
    assert response.status_code == 201
    
    data = response.json()
    assert data["balance"] == initial_deposit
    assert data["available_balance"] == initial_deposit