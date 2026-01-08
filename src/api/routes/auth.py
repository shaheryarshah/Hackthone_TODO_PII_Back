from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.user import User
from schemas.user import UserCreate, UserWithToken
from database import get_db
from services.auth_service import get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserWithToken, status_code=201)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Prevent 409 Conflict Error
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        # 2. Attempt Save
        hashed_pw = get_password_hash(user_data.password)
        new_user = User(email=user_data.email, password_hash=hashed_pw)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
        return UserWithToken(
            id=new_user.id, email=new_user.email, 
            access_token=token, token_type="bearer", created_at=new_user.created_at
        )

    except SQLAlchemyError as e:
        db.rollback()
        # This prevents the silent 500 crash
        raise HTTPException(status_code=500, detail="Database connection failed. Check your environment variables.")
