import pytest
from tests.helpers import (
    generate_unique_email, 
    get_auth_token, 
    create_bank, 
    create_card, 
    get_cards,
    create_user_account
)


def test_create_card(client):
    """Test creating a card"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create bank and account using helpers
    create_bank(client, token)
    account_response = create_user_account(client, token)
    assert account_response.status_code == 201
    
    account_id = account_response.json()["id"]
    
    # Create card using helper
    card_response = create_card(client, token, account_id)
    assert card_response.status_code in [200, 201]
    
    card_data = card_response.json()
    assert "id" in card_data
    assert card_data["card_type"] == "debit"


def test_get_my_cards(client):
    """Test getting all cards for current user"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create bank, account, and card using helpers
    create_bank(client, token)
    account_response = create_user_account(client, token)
    assert account_response.status_code == 201
    
    account_id = account_response.json()["id"]
    
    # Create card using helper
    card_response = create_card(client, token, account_id)
    assert card_response.status_code in [200, 201]
    
    # Get all cards using helper
    cards_response = get_cards(client, token)
    assert cards_response.status_code == 200
    
    cards = cards_response.json()
    assert isinstance(cards, list)
    assert len(cards) >= 1