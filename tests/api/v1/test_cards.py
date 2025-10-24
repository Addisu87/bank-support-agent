# tests/api/v1/test_cards.py
import pytest
import uuid
from tests.helpers import (
    get_auth_token,
    create_user_account,
    create_bank,
    create_card,
    get_cards
)


def generate_unique_email():
    """Generate a unique email for each test run"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_create_card(client):
    """Test creating a card"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # First create a bank
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201
    bank_id = bank_response.json()["id"]
    
    # Create account
    account_response = create_user_account(client, token, "checking", 1000.0)
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]
    
    # Create card
    card_data = {
        "account_id": account_id,
        "bank_id": bank_id,
        "card_number": f"4111{uuid.uuid4().hex[:12]}",
        "card_holder_name": "Test User",
        "card_type": "debit",
        "expiry_date": "2026-12-31",
        "cvv": "123",
        "daily_limit": 2000.0,
        "contactless_enabled": True,
        "international_usage": True
    }
    
    response = create_card(client, token, account_id, card_data)
    
    if response.status_code == 422:
        error_data = response.json()
        print("Validation errors:")
        for error in error_data.get('detail', []):
            print(f"  - {error}")
        pytest.fail("Card creation failed with validation errors")
    
    assert response.status_code == 201
    data = response.json()
    assert data["card_type"] == "debit"
    assert data["status"] == "active"
    assert data["contactless_enabled"] is True


def test_get_account_cards(client):
    """Test getting cards for an account"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create bank, account, and card
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201
    bank_id = bank_response.json()["id"]
    
    account_response = create_user_account(client, token, "checking", 1000.0)
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]
    
    # Create a card
    create_card(client, token, account_id, {
        "account_id": account_id,
        "bank_id": bank_id,
        "card_number": f"5111{uuid.uuid4().hex[:12]}",
        "card_holder_name": "Test User",
        "card_type": "credit",
        "expiry_date": "2026-12-31",
        "cvv": "456"
    })
    
    # Get cards for account
    response = get_cards(client, token, account_id)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_card_types(client):
    """Test different card types"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create bank and account
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201
    bank_id = bank_response.json()["id"]
    
    account_response = create_user_account(client, token, "checking", 1000.0)
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]
    
    # Test different card types
    card_types = ["debit", "credit", "prepaid"]
    
    for card_type in card_types:
        card_data = {
            "account_id": account_id,
            "bank_id": bank_id,
            "card_number": f"4111{uuid.uuid4().hex[:12]}",
            "card_holder_name": "Test User",
            "card_type": card_type,
            "expiry_date": "2026-12-31",
            "cvv": "123"
        }
        
        response = create_card(client, token, account_id, card_data)
        assert response.status_code == 201
        data = response.json()
        assert data["card_type"] == card_type