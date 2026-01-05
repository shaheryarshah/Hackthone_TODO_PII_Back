"""Database connection and session management."""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Support both SQLite (dev) and PostgreSQL/Neon (prod)
_db_path = Path(__file__).parent.parent / "todos.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_db_path}"
)

# For SQLite development
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # For PostgreSQL/Neon - use psycopg2 or asyncpg
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy tables
Base = declarative_base()


def get_db() -> Generator:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import models to ensure they're registered with Base
    # Import Todo first since User has a relationship to it
    from models.todo import Todo  # noqa: F401
    from models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
