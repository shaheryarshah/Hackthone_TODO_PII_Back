"""FastAPI application for Todo management."""
import os
import sys
from pathlib import Path

# Add src to path for imports
_src_path = Path(__file__).parent
sys.path.insert(0, str(_src_path))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(_src_path.parent / ".env")

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine, Base
from models.todo import Todo
from models.user import User
from schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from services.todo_service import TodoService
from api.routes.auth import router as auth_router
from middleware.auth import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Todo API",
    description="REST API for managing todo items with extended features",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3006", "http://localhost:3007"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router, prefix="/api/v1")


def _calculate_overdue(todo: Todo) -> bool:
    """Calculate if a todo is overdue."""
    if todo.due_date is None or todo.completed:
        return False
    return todo.due_date < datetime.utcnow()


def _todo_to_response(todo: Todo) -> TodoResponse:
    """Convert Todo model to TodoResponse schema."""
    response_data = {
        "id": todo.id,
        "user_id": todo.user_id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "priority": todo.priority,
        "tags": todo.tags,
        "due_date": todo.due_date,
        "recurrence": todo.recurrence,
        "created_at": todo.created_at,
        "updated_at": todo.updated_at,
        "overdue": _calculate_overdue(todo)
    }
    return TodoResponse(**response_data)


@app.get("/api/v1/todos", response_model=TodoListResponse)
def get_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search in title and description"),
    status: Optional[str] = Query(None, pattern="^(completed|pending)$", description="Filter by status"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high)$", description="Filter by priority"),
    due_before: Optional[datetime] = Query(None, description="Filter todos due before this date"),
    due_after: Optional[datetime] = Query(None, description="Filter todos due after this date"),
    tag: Optional[str] = Query(None, description="Filter by specific tag"),
    sort_by: Optional[str] = Query("created_at", pattern="^(created_at|due_date|priority|title)$", description="Sort field"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
):
    """Get all todos with optional search, filtering, and sorting."""
    service = TodoService(db, user_id=current_user.id)
    todos = service.get_all(
        search=search,
        status=status,
        priority=priority,
        due_before=due_before,
        due_after=due_after,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Convert to response schema with overdue calculation
    todos_response = [_todo_to_response(todo) for todo in todos]

    return {
        "todos": todos_response,
        "count": len(todos_response),
        "has_more": False  # Pagination not implemented yet
    }


@app.post("/api/v1/todos", response_model=TodoResponse, status_code=201)
def create_todo(
    todo_data: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new todo with optional extended fields."""
    try:
        service = TodoService(db, user_id=current_user.id)
        todo = service.create(todo_data)
        return _todo_to_response(todo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/todos/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single todo by ID."""
    service = TodoService(db, user_id=current_user.id)
    todo = service.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return _todo_to_response(todo)


@app.put("/api/v1/todos/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a todo with optional extended fields."""
    try:
        service = TodoService(db, user_id=current_user.id)
        todo = service.update(todo_id, todo_data)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return _todo_to_response(todo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a todo."""
    service = TodoService(db, user_id=current_user.id)
    if not service.delete(todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted successfully"}


@app.patch("/api/v1/todos/{todo_id}/complete")
def mark_todo_complete(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a todo as complete.
    If the todo has a recurrence pattern, automatically creates the next instance.
    Returns both the completed task and the next task (if applicable).
    """
    service = TodoService(db, user_id=current_user.id)
    result = service.mark_complete(todo_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    completed_task, next_task = result

    response = {
        "completed_task": _todo_to_response(completed_task)
    }

    if next_task:
        response["next_task"] = _todo_to_response(next_task)

    return response


@app.get("/api/v1/todos/due-soon")
def get_todos_due_soon(
    hours: int = Query(1, ge=1, le=24, description="Number of hours to look ahead"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get todos due within the specified hours for reminder notifications."""
    service = TodoService(db, user_id=current_user.id)
    todos = service.get_todos_due_soon(hours=hours)
    todos_response = [_todo_to_response(todo) for todo in todos]
    return {"todos": todos_response, "count": len(todos_response)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
