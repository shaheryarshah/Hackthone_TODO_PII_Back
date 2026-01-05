"""Todo SQLModel entity with user ownership."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
from models.enums import Priority, RecurrencePattern


class Todo(Base):
    """Todo entity representing a task item owned by a user."""

    __tablename__ = "todos_001_todo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users_001_todo.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(String(5000), nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Extended fields for Phase II features
    priority = Column(String(10), nullable=True)  # LOW, MEDIUM, HIGH
    tags = Column(JSON, nullable=True)  # Array of strings
    due_date = Column(DateTime, nullable=True)
    recurrence = Column(String(10), nullable=True)  # NONE, DAILY, WEEKLY, MONTHLY

    # Relationship to user - enables ownership queries
    user = relationship("User", back_populates="todos")

    def __repr__(self) -> str:
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.completed}, user_id={self.user_id})>"
