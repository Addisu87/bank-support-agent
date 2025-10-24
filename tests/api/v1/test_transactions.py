# tests/api/v1/test_transactions.py
import pytest
import uuid
from tests.helpers import (
    get_auth_token,
    create_user_account,
    create_transaction,
    get_transactions
)


def generate_unique_email():
    """Generate a unique email for each test run"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_create_transaction(client):
    """Test creating a transaction"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # First create an account
    account_response = create_user_account(client, token, "checking", 1000.0)
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]
    
    # Create transaction
    transaction_data = {
        "account_id": account_id,
        "amount": 100.0,
        "transaction_type": "deposit",
        "description": "Test deposit transaction",
        "merchant": "Test Merchant",
        "merchant_category": "Retail"
    }
    
    response = create_transaction(client, token, account_id, transaction_data)
    
    if response.status_code == 422:
        error_data = response.json()
        print("Validation errors:")
        for error in error_data.get('detail', []):
            print(f"  - {error}")
        pytest.fail("Transaction creation failed with validation errors")
    
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 100.0
    assert data["transaction_type"] == "deposit"
    assert data["status"] == "completed"  # or "pending" depending on your logic


def test_get_account_transactions(client):
    """Test getting transactions for an account"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create account and transaction
    account_response = create_user_account(client, token, "checking", 1000.0)
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]
    
    # Create a transaction
    create_transaction(client, token, account_id)
    
    # Get transactions for account
    response = get_transactions(client, token, account_id)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_transaction_types(client):
    """Test different transaction types"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create account
    account_response = create_user_account(client, token, "checking", 1000.0)
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]
    
    # Test different transaction types
    transaction_types = ["deposit", "withdrawal", "transfer", "payment"]
    
    for txn_type in transaction_types:
        transaction_data = {
            "account_id": account_id,
            "amount": 50.0,
            "transaction_type": txn_type,
            "description": f"Test {txn_type} transaction"
        }
        
        response = create_transaction(client, token, account_id, transaction_data)
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == txn_type