"""FastAPI dependencies for authentication and database."""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from services.auth_service import decode_access_token


def get_current_user(
    credentials: Annotated[str | None, Depends(
        "get_authorization_header"
    )] = None,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    # Extract token from "Bearer <token>" format
    if not credentials.startswith("Bearer "):
        raise credentials_exception

    token = credentials.replace("Bearer ", "")
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_authorization_header(
    authorization: str | None = None
) -> str | None:
    """
    Extract the authorization header value.

    This is a separate function to allow dependency injection.
    """
    if authorization is None:
        return None
    return authorization


async def get_current_user_async():
    """Async version of get_current_user for future async implementation."""
    # TODO: Implement async version with asyncpg/SQLModel async
    pass


class AuthError(Exception):
    """Custom authentication error."""

    def __init__(self, detail: str):
        self.detail = detail
