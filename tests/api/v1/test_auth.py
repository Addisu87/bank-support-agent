# tests/api/v1/test_auth.py
import pytest
from tests.helpers import (
    register_user,
    login_user,
    get_auth_token,
)
from fastapi import status 
import uuid


def generate_unique_email():
    """Generate a unique email for each test run"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_register_user_success(client):
    """Test successful user registration"""
    email = generate_unique_email()  # Use unique email
    password = "password123"
    data = {
        "email": email, 
        "password": password,
        "full_name": "Test User",
        "phone_number": "+1234567890"
    }
    response = client.post("/api/v1/auth/register", json=data)

    print(f"Registration Response: {response.status_code} - {response.text}")
    
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert result["email"] == email
    assert "id" in result


def test_login_success(client):
    """Test successful login after registration"""
    # Use unique email
    email = generate_unique_email()
    user_data = {
        "email": email,
        "password": "testpassword123",
        "full_name": "Test User", 
        "phone_number": "+1234567890"
    }
    register_response = client.post("/api/v1/auth/register", json=user_data)
    print(f"Registration for login: {register_response.status_code} - {register_response.text}")
    
    assert register_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
    
    # Then login
    login_response = login_user(client, email, "testpassword123")
    print(f"Login Response: {login_response.status_code} - {login_response.text}")
    
    assert login_response.status_code == status.HTTP_200_OK
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_invalid_password(client):
    """Test login with wrong password"""
    # Use unique email
    email = generate_unique_email()
    register_response = register_user(client, email)
    
    # Try login with wrong password
    login_response = login_user(client, email, "wrongpassword")
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    # Use unique email that definitely doesn't exist
    email = f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
    login_response = login_user(client, email, "somepassword")
    
    print(f"Non-existent user Response: {login_response.status_code} - {login_response.text}")
    
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_missing_fields(client):
    """Test registration with missing required fields"""
    # Use unique email
    email = generate_unique_email()
    # Missing password
    user_data = {
        "email": email,
        "full_name": "Test User",
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_auth_token_helper(client):
    """Test the auth token helper function"""
    # Use unique email
    email = generate_unique_email()
    # First register a user
    register_user(client, email)
    
    # Then get token
    token = get_auth_token(client, email)
    
    assert isinstance(token, str)
    assert len(token) > 0