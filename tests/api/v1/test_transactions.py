import pytest
from tests.helpers import (
    generate_unique_email,
    get_auth_token,
    create_bank,
    create_user_account,
    create_transaction,
    get_transactions,
)


@pytest.mark.asyncio
async def test_create_transaction(client):
    """Test creating a transaction"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)

    # Create bank and account using helpers
    await create_bank(client, token)
    account_response = await create_user_account(client, token)
    assert account_response.status_code == 201

    account_id = account_response.json()["id"]

    # Create transaction using helper
    transaction_response = await create_transaction(client, token, account_id)
    assert transaction_response.status_code == 201

    transaction_data = transaction_response.json()
    assert transaction_data["amount"] == 100.0
    assert transaction_data["transaction_type"] == "deposit"
    assert "id" in transaction_data


@pytest.mark.asyncio
async def test_get_transactions_with_account_filter(client):
    """Test getting transactions with account filter"""
    email = generate_unique_email()
    token = await get_auth_token(client, email)

    # Create bank and account using helpers
    await create_bank(client, token)
    account_response = await create_user_account(client, token)
    assert account_response.status_code == 201

    account_id = account_response.json()["id"]

    # Create transaction using helper
    await create_transaction(client, token, account_id)

    # Get transactions with account filter using helper
    transactions_response = await get_transactions(client, token, account_id=account_id)
    assert transactions_response.status_code == 200

    transactions = transactions_response.json()
    assert isinstance(transactions, list)
    assert len(transactions) >= 1
