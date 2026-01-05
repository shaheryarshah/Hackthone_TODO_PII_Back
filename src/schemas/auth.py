"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class ErrorResponse(BaseModel):
    """Schema for API error response."""

    detail: str


class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str
