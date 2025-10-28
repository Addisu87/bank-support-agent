import pytest
from fastapi import status 
import uuid
from tests.helpers import (
    generate_unique_email,
    register_user,
    login_user,
    get_auth_token,
)


@pytest.mark.asyncio
async def test_register_user_success(client):
    """Test successful user registration"""
    email = generate_unique_email()  
    password = "password123"
    data = {
        "email": email, 
        "password": password,
        "full_name": "Test User",
        "phone_number": "+1234567890"
    }
    response = await client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert result["email"] == email
    assert "id" in result


@pytest.mark.asyncio
async def test_login_success(client):
    """Test successful login after registration"""
    email = generate_unique_email()
    user_data = {
        "email": email,
        "password": "testpassword123",
        "full_name": "Test User", 
        "phone_number": "+1234567890"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert register_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
    
    # Then login
    login_response = await login_user(client, email, "testpassword123")
    
    assert login_response.status_code == status.HTTP_200_OK
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    """Test login with wrong password"""
    email = generate_unique_email()

    
    # Try login with wrong password
    login_response = await login_user(client, email, "wrongpassword")
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    # Use unique email that definitely doesn't exist
    email = f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
    login_response = await login_user(client, email, "somepassword")
    
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_register_missing_fields(client):
    """Test registration with missing required fields"""
    # Use unique email
    email = generate_unique_email()
    # Missing password
    user_data = {
        "email": email,
        "full_name": "Test User",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_auth_token_helper(client):
    """Test the auth token helper function"""
    # Use unique email
    email = generate_unique_email()
    # First register a user
    await register_user(client, email)
    
    # Then get token
    token = await get_auth_token(client, email)
    
    assert isinstance(token, str)
    assert len(token) > 0