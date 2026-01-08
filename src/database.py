"""Database connection and session management."""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. FIX: Handle connection string format
DATABASE_URL = os.getenv("DATABASE_URL")

# If no environment variable is found, fallback to local SQLite
if not DATABASE_URL:
    _db_path = Path(__file__).parent.parent / "todos.db"
    DATABASE_URL = f"sqlite:///{_db_path}"

# FIX: SQLAlchemy requires 'postgresql://', but some providers give 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Configure Engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True, # Keeps connection alive
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    from models.todo import Todo  # noqa: F401
    from models.user import User  # noqa: F401
    Base.metadata.create_all(bind=engine)
