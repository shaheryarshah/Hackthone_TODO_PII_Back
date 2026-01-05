"""Authentication API routes for registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserCreate, UserLogin, UserResponse, UserWithToken
from schemas.auth import TokenResponse, ErrorResponse
from schemas.auth import ErrorResponse as AuthErrorResponse
from services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_token_expiry_seconds
)
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserWithToken,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
    summary="Register a new user",
    description="Creates a new user account and returns JWT token"
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)) -> UserWithToken:
    """
    Register a new user with email and password.

    - **email**: Valid email address (must be unique)
    - **password**: At least 8 characters

    Returns user info and JWT access token.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new user with hashed password
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    token_data = {"sub": str(new_user.id), "email": new_user.email}
    access_token = create_access_token(token_data)

    return UserWithToken(
        id=new_user.id,
        email=new_user.email,
        created_at=new_user.created_at,
        access_token=access_token,
        token_type="bearer"
    )


@router.post(
    "/login",
    response_model=UserWithToken,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
    },
    summary="Login user",
    description="Authenticates user and returns JWT token"
)
async def login(credentials: UserLogin, db: Session = Depends(get_db)) -> UserWithToken:
    """
    Login with email and password.

    - **email**: Registered email address
    - **password**: User's password

    Returns user info and JWT access token on success.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate JWT token
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)

    return UserWithToken(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        access_token=access_token,
        token_type="bearer"
    )
