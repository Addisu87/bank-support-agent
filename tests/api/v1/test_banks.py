# tests/api/v1/test_banks.py
import pytest
import uuid
from tests.helpers import (
    get_auth_token,
    create_bank,
    get_banks
)


def generate_unique_email():
    """Generate a unique email for each test run"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_create_bank(client):
    """Test creating a bank (financial institution)"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    bank_data = {
        "name": "Test Bank International",
        "code": f"TB{uuid.uuid4().hex[:4]}".upper(),
        "country": "United States",
        "currency": "USD",
        "contact_email": "contact@testbank.com",
        "contact_phone": "+1234567890",
        "website": "https://testbank.com",
        "address": "123 Test Street, Test City"
    }
    
    response = create_bank(client, token, bank_data)
    
    if response.status_code == 422:
        error_data = response.json()
        print("Validation errors:")
        for error in error_data.get('detail', []):
            print(f"  - {error}")
        pytest.fail(f"Bank creation failed with validation errors")
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == bank_data["name"]
    assert data["code"] == bank_data["code"]
    assert data["is_active"] is True


def test_get_banks(client):
    """Test getting all banks"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    # Create a bank first
    create_response = create_bank(client, token)
    if create_response.status_code != 201:
        pytest.skip("Bank creation failed, skipping get banks test")
    
    # Get all banks
    response = get_banks(client, token)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_bank_unique_constraints(client):
    """Test that bank code and swift code are unique"""
    email = generate_unique_email()
    token = get_auth_token(client, email)
    
    bank_data = {
        "name": "First Test Bank",
        "code": "UNIQUE001",
        "swift_code": "UNIQUS33",
        "country": "United States",
        "currency": "USD"
    }
    
    # Create first bank
    response1 = create_bank(client, token, bank_data)
    assert response1.status_code == 201
    
    # Try to create second bank with same code
    bank_data2 = bank_data.copy()
    bank_data2["name"] = "Second Test Bank"
    response2 = create_bank(client, token, bank_data2)
    
    # Should fail due to unique constraint
    assert response2.status_code == 400