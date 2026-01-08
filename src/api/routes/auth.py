from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from models.user import User
from schemas.user import UserCreate, UserLogin, UserWithToken
from services.auth_service import get_password_hash, verify_password, create_access_token
from database import get_db

# Log errors to your console/terminal
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. First, check if email is already taken (Prevents 409 Conflict)
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    try:
        # 2. Hash password and create User instance
        # Ensure your User model has 'password_hash' as a column!
        hashed_pw = get_password_hash(user_data.password)
        new_user = User(email=user_data.email, password_hash=hashed_pw)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 3. Create Login Token
        token = create_access_token({"sub": str(new_user.id), "email": new_user.email})

        return UserWithToken(
            id=new_user.id,
            email=new_user.email,
            created_at=new_user.created_at,
            access_token=token,
            token_type="bearer"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database failed to save user. Check if columns match."
        )
    except Exception as e:
        logger.error(f"General Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )

@router.post("/login", response_model=UserWithToken)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return UserWithToken(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        access_token=token,
        token_type="bearer"
    )
