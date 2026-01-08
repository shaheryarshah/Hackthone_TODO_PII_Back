from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select  # For async, but keeping sync for now if you're using sync session

from models.user import User
from schemas.user import UserCreate, UserLogin, UserWithToken
from database import get_db
from services.auth_service import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    Returns user data with access token.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    try:
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            # username=user_data.username,  # Uncomment if your User model has username
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(new_user.id), "email": new_user.email}
        )

        return UserWithToken(
            id=new_user.id,
            email=new_user.email,
            access_token=access_token,
            token_type="bearer",
            created_at=new_user.created_at
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Database error occurred."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration."
        )


@router.post("/login", response_model=UserWithToken)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return access token.
    """
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    return UserWithToken(
        id=user.id,
        email=user.email,
        access_token=access_token,
        token_type="bearer",
        created_at=user.created_at
    )
