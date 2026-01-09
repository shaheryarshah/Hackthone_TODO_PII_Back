from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    completed: Optional[bool] = False
    priority: Optional[str] = "medium"
    tags: Optional[List[str]] = []
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None

    @validator("completed", pre=True)
    def parse_completed(cls, v):
        """Allow boolean-like strings from frontend."""
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes"]
        return v

    @validator("priority", pre=True)
    def parse_priority(cls, v):
        """Normalize priority to lower-case and valid values."""
        if not v:
            return "medium"
        v = v.lower()
        if v not in ["low", "medium", "high"]:
            raise ValueError("Priority must be low, medium, or high")
        return v

class TodoCreate(TodoBase):
    pass  # inherits all fields

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None

    @validator("completed", pre=True)
    def parse_completed(cls, v):
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes"]
        return v

    @validator("priority", pre=True)
    def parse_priority(cls, v):
        if not v:
            return None
        v = v.lower()
        if v not in ["low", "medium", "high"]:
            raise ValueError("Priority must be low, medium, or high")
        return v

class TodoResponse(TodoBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    overdue: bool = False

class TodoListResponse(BaseModel):
    todos: List[TodoResponse]
    count: int
    has_more: bool
