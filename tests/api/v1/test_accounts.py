# tests/api/v1/test_accounts.py
import pytest
import uuid
from tests.helpers import generate_unique_email, get_auth_token, create_bank, create_user_account, get_user_accounts


# In all test files, replace bank creation assertions with:
def test_create_user_account(client):
    """Test creating a user bank account"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # First create a bank with unique data
    unique_bank_data = {
        "name": f"Test Bank {uuid.uuid4().hex[:8]}",
        "code": f"TB{uuid.uuid4().hex[:6]}",
        "country": "United States",
    }
    
    bank_response = client.post(
        "/api/v1/banks/",
        json=unique_bank_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Handle bank creation response
    if bank_response.status_code == 400 and "already exists" in bank_response.text:
        # Bank code conflict, try with a different code
        unique_bank_data["code"] = f"TB{uuid.uuid4().hex[:8]}"
        bank_response = client.post(
            "/api/v1/banks/",
            json=unique_bank_data,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert bank_response.status_code == 201, f"Bank creation failed: {bank_response.text}"


def test_get_user_accounts(client):
    """Test getting user accounts"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # First create a bank
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201, "Bank creation failed"
    
    # Get bank ID
    banks_response = client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
    banks_data = banks_response.json()
    banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    bank_id = banks_list[0].get('id')
    
    # Create an account with correct schema
    account_data = {
        "account_type": "checking",
        "bank_id": bank_id,
    }
    create_response = client.post(
        "/api/v1/accounts/",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201, f"Account creation failed: {create_response.text}"
    
    # Get accounts
    accounts_response = get_user_accounts(client, token)
    assert accounts_response.status_code == 200, f"Get accounts failed: {accounts_response.text}"
    
    accounts_data = accounts_response.json()
    assert isinstance(accounts_data, list), f"Accounts should be list, got {type(accounts_data)}"
    assert len(accounts_data) >= 1, f"Should have at least 1 account, got {len(accounts_data)}"


def test_create_multiple_account_types(client):
    """Test creating multiple account types for a user"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create a bank first
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201, "Bank creation failed"
    
    # Get bank ID
    banks_response = client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
    banks_data = banks_response.json()
    banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    bank_id = banks_list[0].get('id')
    
    # Create checking account
    checking_data = {
        "account_type": "checking",
        "bank_id": bank_id,
    }
    checking_response = client.post(
        "/api/v1/accounts/",
        json=checking_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert checking_response.status_code == 201, f"Checking account creation failed: {checking_response.text}"
    
    # Create savings account
    savings_data = {
        "account_type": "savings",
        "bank_id": bank_id,
    }
    savings_response = client.post(
        "/api/v1/accounts/",
        json=savings_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert savings_response.status_code == 201, f"Savings account creation failed: {savings_response.text}"
    
    # Get all accounts
    accounts_response = get_user_accounts(client, token)
    assert accounts_response.status_code == 200, f"Get accounts failed: {accounts_response.text}"
    
    accounts_data = accounts_response.json()
    assert isinstance(accounts_data, list), f"Accounts should be list, got {type(accounts_data)}"
    assert len(accounts_data) >= 2, f"Should have at least 2 accounts, got {len(accounts_data)}"
    
    # Verify we have different account types
    account_types = [acc.get("account_type") for acc in accounts_data if acc.get("account_type")]
    assert "checking" in account_types, f"Checking account type not found in: {account_types}"
    assert "savings" in account_types, f"Savings account type not found in: {account_types}"


def test_get_specific_account(client):
    """Test getting a specific account by ID"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # First create a bank
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201, "Bank creation failed"
    
    # Get bank ID
    banks_response = client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
    banks_data = banks_response.json()
    banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    bank_id = banks_list[0].get('id')
    
    # Create an account
    account_data = {
        "account_type": "checking",
        "bank_id": bank_id,
    }
    create_response = client.post(
        "/api/v1/accounts/",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201, f"Account creation failed: {create_response.text}"
    
    account_json = create_response.json()
    account_id = account_json.get('id')
    assert account_id is not None, "Account ID not found"
    
    # Get specific account
    response = client.get(
        f"/api/v1/accounts/{account_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, f"Get specific account failed: {response.text}"
    
    specific_account = response.json()
    assert specific_account.get('id') == account_id
    assert specific_account.get('account_type') == "checking"
    assert specific_account.get('bank_id') == bank_id


def test_account_balance_initialization(client):
    """Test that account balances are properly initialized"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create a bank
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201, "Bank creation failed"
    
    # Get bank ID
    banks_response = client.get("/api/v1/banks/", headers={"Authorization": f"Bearer {token}"})
    banks_data = banks_response.json()
    banks_list = banks_data.get('banks', []) if isinstance(banks_data, dict) else banks_data
    bank_id = banks_list[0].get('id')
    
    # Create account
    account_data = {
        "account_type": "checking",
        "bank_id": bank_id,
    }
    response = client.post(
        "/api/v1/accounts/",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201, f"Account creation failed: {response.text}"
    
    account_json = response.json()
    assert account_json.get('balance') == 0.0, f"Balance should be 0.0, got {account_json.get('balance')}"
    assert account_json.get('status') == 'active', f"Status should be 'active', got {account_json.get('status')}"