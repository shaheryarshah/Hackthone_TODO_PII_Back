"""User Pydantic schemas for registration, login, and responses."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """Schema for user registration request."""

    email: EmailStr = Field(..., description="User's email address (will be unique)")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User's registered email")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Schema for user data returned from API (excludes password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class UserWithToken(UserResponse):
    """Schema for user response with JWT token."""

    access_token: str
    token_type: str = "bearer"
