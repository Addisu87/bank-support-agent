import pytest
import uuid
from tests.helpers import (
    generate_unique_email,
    get_auth_token,
    create_bank,
    get_banks
)


def test_create_bank(client):
    """Test creating a bank"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    bank_data = {
        "name": "Test Bank International",
        "code": f"tb{uuid.uuid4().hex[:4]}",
        "country": "United States",
        "currency": "USD",
    }
    
    response = client.post(
        "/api/v1/banks/",
        json=bank_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201, f"Bank creation failed: {response.text}"
    
    bank_response = response.json()
    assert bank_response.get("name") == bank_data["name"]
    assert bank_response.get("code") == bank_data["code"].upper()
    assert bank_response.get("country") == bank_data["country"]


def test_get_banks(client):
    """Test getting all banks"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create a bank first
    bank_response = create_bank(client, token)
    assert bank_response.status_code == 201, "Bank creation failed"
    
    # Get all banks
    banks_response = get_banks(client, token)
    assert banks_response.status_code == 200, f"Get banks failed: {banks_response.text}"
    
    banks_data = banks_response.json()
    
    # Handle the actual response format (dictionary with 'banks' key)
    assert isinstance(banks_data, dict), "Banks response should be a dictionary"
    assert 'banks' in banks_data, "Banks response should contain 'banks' key"
    
    banks_list = banks_data['banks']
    assert isinstance(banks_list, list), "Banks should be a list"
    assert len(banks_list) >= 1, "Should have at least 1 bank"


def test_create_bank_unique_constraints(client):
    """Test that bank code is unique"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    unique_code = f"uniq{uuid.uuid4().hex[:4]}"
    
    bank_data = {
        "name": "First Test Bank",
        "code": unique_code,
        "country": "United States",
    }
    
    # Create first bank
    response1 = client.post(
        "/api/v1/banks/",
        json=bank_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response1.status_code == 201, "First bank creation failed"
    
    # Try to create second bank with same code
    bank_data2 = {
        "name": "Second Test Bank",
        "code": unique_code,  # Same code
        "country": "United States",
    }
    response2 = client.post(
        "/api/v1/banks/",
        json=bank_data2,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should fail due to unique code constraint
    assert response2.status_code in [400, 409, 422], f"Expected unique constraint error, got {response2.status_code}"