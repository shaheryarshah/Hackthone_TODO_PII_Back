"""Authentication API routes for registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from models.user import User
from schemas.user import UserCreate, UserLogin, UserWithToken
from schemas.auth import ErrorResponse
from services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token
)
from database import get_db

# Setup logging to catch the cause of 500 errors in your terminal
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=UserWithToken,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    summary="Register a new user"
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)) -> UserWithToken:
    """
    Register a new user. 
    Handles 409 Conflicts and prevents 500 crashes.
    """
    # 1. Check if email already exists to avoid 409 Conflict
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered. Please login instead."
        )

    try:
        # 2. Hash password and create user object
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password
        )
        
        # 3. Database Transaction
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 4. Generate JWT token
        token_data = {"sub": str(new_user.id), "email": new_user.email}
        access_token = create_access_token(token_data)

        return UserWithToken(
            id=new_user.id,
            email=new_user.email,
            created_at=new_user.created_at,
            access_token=access_token,
            token_type="bearer"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred on the server."
        )

@router.post(
    "/login",
    response_model=UserWithToken,
    summary="Login user"
)
async def login(credentials: UserLogin, db: Session = Depends(get_db)) -> UserWithToken:
    """Authenticates user and returns JWT token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Verify user exists and password is correct
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate token
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)

    return UserWithToken(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        access_token=access_token,
        token_type="bearer"
    )
