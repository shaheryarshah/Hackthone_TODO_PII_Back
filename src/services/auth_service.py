"""Authentication service for password hashing and JWT token management."""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt


class AuthService:
    """Service for authentication-related operations."""

    @classmethod
    def get_secret_key(cls) -> str:
        """Get JWT secret key from environment."""
        return os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")  # noqa: S105

    @classmethod
    def get_algorithm(cls) -> str:
        """Get JWT algorithm from environment."""
        return os.getenv("JWT_ALGORITHM", "HS256")

    @classmethod
    def get_expiration_minutes(cls) -> int:
        """Get token expiration in minutes from environment."""
        return int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        # bcrypt.hashpw() with gensalt() returns: "version$salt$hash"
        # bcrypt.checkpw() needs the FULL hash with salt embedded
        # So we just pass the hashed password directly
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        """Hash a password using bcrypt."""
        # Use bcrypt.hashpw() with gensalt() which properly handles salting
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        # Return the FULL hash with salt (version$salt$hash)
        # This is what bcrypt.checkpw() expects
        return hashed.decode('utf-8')

    @classmethod
    def create_access_token(
        cls,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=cls.get_expiration_minutes())
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            cls.get_secret_key(),
            algorithm=cls.get_algorithm()
        )
        return encoded_jwt

    @classmethod
    def decode_access_token(cls, token: str) -> Optional[dict]:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                cls.get_secret_key(),
                algorithms=[cls.get_algorithm()]
            )
            return payload
        except JWTError:
            return None

    @classmethod
    def get_token_expiry_seconds(cls) -> int:
        """Get token expiry time in seconds."""
        return cls.get_expiration_minutes() * 60


# Convenience functions for use in routes
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return AuthService.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return AuthService.get_password_hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    return AuthService.create_access_token(data, expires_delta)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    return AuthService.decode_access_token(token)


def get_token_expiry_seconds() -> int:
    """Get token expiry time in seconds."""
    return AuthService.get_token_expiry_seconds()
