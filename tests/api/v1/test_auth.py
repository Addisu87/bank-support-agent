# Auth tests, registration/login/refresh/logout

import pytest
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_register_user(client, test_session):
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "phone_number": "+1234567890"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "password" not in data

@pytest.mark.asyncio
async def test_login_user(client, test_session):
    # First register
    user_data = {
        "email": "login@example.com",
        "password": "testpassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "username": "login@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"