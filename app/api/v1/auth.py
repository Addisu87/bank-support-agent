import logfire
from fastapi import APIRouter, HTTPException, status
from app.models.user import UserIn, UserLogin, LoginResponse, RegisterResponse, UserResponse
from app.services.user_service import get_user_by_email, create_user
from app.core.deps import (
    authenticate_user,
    issue_tokens_for_user
)

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse)
async def register(user: UserIn):
    """Register a new user account."""
    existing_user = await get_user_by_email(email=user.email)
    if existing_user:
        logfire.info("User already exists!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists!",
        )
    
    new_user = await create_user(user.email, user.password, user.full_name)
    
    if not new_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    return RegisterResponse(
        status="success",
        message="User registered successfully",
        user=UserResponse(
            id=new_user.id, # type: ignore
            email=new_user.email, # type: ignore
            full_name=new_user.full_name, # type: ignore
            roles=new_user.roles or [], # type: ignore
            created_at=new_user.created_at.isoformat() if new_user.created_at is not None else None
        )
    )
    
    
@router.post("/token", response_model=LoginResponse)
async def login(form_data: UserLogin):
    """Login user and return complete user information with tokens."""
    logfire.info(f"User login attempt: {form_data.email}")
    
    auth_user = await authenticate_user(form_data.email, form_data.password)
    if not auth_user: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token, refresh_token = await issue_tokens_for_user(auth_user)
    
    logfire.info(f"User logged in successfully: {auth_user.email}")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=auth_user.id,
            email=auth_user.email,
            full_name=auth_user.full_name,
            roles=auth_user.roles or [],
            created_at=auth_user.created_at.isoformat() if auth_user.created_at is not None else None
        )
    )

    
    
    
    