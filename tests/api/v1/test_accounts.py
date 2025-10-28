import pytest
import uuid
from tests.helpers import (
    generate_unique_email,
    get_auth_token,
    create_bank, 
    create_user_account,
    get_user_accounts
)


# In all test files, replace bank creation assertions with:
@pytest.mark.asyncio
async def test_create_user_account(client):
    """Test creating a user bank account using helpers"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)
    
    # Create a bank first
    await create_bank(client, token)
    
    # Use the fixed helper - it will get the bank ID automatically
    account_response = await create_user_account(client, token)
    assert account_response.status_code == 201


@pytest.mark.asyncio
async def test_get_user_accounts(client):
    """Test getting user accounts"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)
    
    # Create bank and account using helpers
    await create_bank(client, token)
    await create_user_account(client, token)
    
    # Get accounts
    accounts_response = await get_user_accounts(client, token)
    assert accounts_response.status_code == 200
    assert len(accounts_response.json()) >= 1


@pytest.mark.asyncio
async def test_create_multiple_account_types(client):
    """Test creating multiple account types"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)
    
    await create_bank(client, token)
    
    # Create multiple accounts using the fixed helper
    await create_user_account(client, token, account_type="checking")
    await create_user_account(client, token, account_type="savings")
    
    accounts = (await get_user_accounts(client, token)).json()
    assert len(accounts) >= 2
    account_types = [acc["account_type"] for acc in accounts]
    assert "checking" in account_types
    assert "savings" in account_types


@pytest.mark.asyncio
async def test_get_specific_account(client):
    """Test getting a specific account by ID"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)
    
    await create_bank(client, token)
    
    # Create account using the fixed helper
    account_response = await create_user_account(client, token)
    account_id = account_response.json()["id"]
    
    # Get specific account
    response = await client.get(f"/api/v1/accounts/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    specific_account = response.json()
    assert specific_account["id"] == account_id
    assert specific_account["account_type"] == "checking"


@pytest.mark.asyncio
async def test_account_balance_initialization(client):
    """Test that account balances are properly initialized"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)
    
    await create_bank(client, token)
    
    account_response = await create_user_account(client, token)
    account_data = account_response.json()
    
    assert account_data["balance"] == 0.0
    assert account_data["status"] == "active"