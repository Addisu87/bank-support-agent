
import jwt 
from passlib.context import CryptContext
from bank_agent.core.config import settings
from bank_agent.utils.constants import (
    access_token_expire_minutes,
    confirm_token_expire_minutes
)
from datetime import datetime, timedelta, timezone


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(email: str, roles: list = None):
    """Create access token"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=access_token_expire_minutes()
    )
    to_encode = {"sub": email, "roles": roles or [], "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(email: str):
    """Create a refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=confirm_token_expire_minutes()
    )
    to_encode = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)
    
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

