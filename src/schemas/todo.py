"""Pydantic schemas for Todo with user ownership."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TodoCreate(BaseModel):
    """Schema for creating a new todo (user_id set from JWT, not request body)."""

    title: str = Field(..., min_length=1, max_length=500, description="Task title (required)")
    description: Optional[str] = Field(None, max_length=5000, description="Optional details")
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high)$", description="Task priority")
    tags: Optional[List[str]] = Field(None, description="Task tags (max 10, max 50 chars each)")
    due_date: Optional[datetime] = Field(None, description="Due date and time (ISO 8601 UTC)")
    recurrence: Optional[str] = Field("none", pattern="^(none|daily|weekly|monthly)$", description="Recurrence pattern")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags array."""
        if v is None:
            return v
        # Ensure max 10 tags
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        # Ensure no duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate tags are not allowed")
        # Validate each tag
        for tag in v:
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds maximum length of 50 characters")
            # Check for invalid characters
            if not all(c.isalnum() or c in ' -_' for c in tag):
                raise ValueError(f"Tag '{tag}' contains invalid characters")
        return v

    @field_validator('recurrence')
    @classmethod
    def validate_recurrence_requires_due_date(cls, v, info):
        """Ensure recurrence requires due_date."""
        if v and v != "none":
            due_date = info.data.get('due_date')
            if due_date is None:
                raise ValueError("recurrence requires due_date to be set")
        return v


class TodoUpdate(BaseModel):
    """Schema for updating a todo."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = Field(None, pattern="^(none|daily|weekly|monthly)$")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags array."""
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate tags are not allowed")
        for tag in v:
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds maximum length of 50 characters")
            if not all(c.isalnum() or c in ' -_' for c in tag):
                raise ValueError(f"Tag '{tag}' contains invalid characters")
        return v

    @field_validator('recurrence')
    @classmethod
    def validate_recurrence_requires_due_date(cls, v, info):
        """Ensure recurrence requires due_date."""
        if v and v != "none":
            due_date = info.data.get('due_date')
            # For update, we also need to check if due_date is being set to None
            if due_date is None:
                raise ValueError("recurrence requires due_date to be set")
        return v


class TodoResponse(BaseModel):
    """Schema for todo response including owner user_id."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    overdue: Optional[bool] = False


class TodoListResponse(BaseModel):
    """Schema for list of todos response."""

    todos: List[TodoResponse]
    count: int
    has_more: bool = False
