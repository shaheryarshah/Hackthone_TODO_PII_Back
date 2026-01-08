"""FastAPI application for Todo management."""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add src to path for imports
_src_path = Path(__file__).parent
sys.path.insert(0, str(_src_path))

# Load environment variables
load_dotenv(_src_path.parent / ".env")

from database import get_db, engine, Base
from models.todo import Todo
from models.user import User
from schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from services.todo_service import TodoService
from api.routes.auth import router as auth_router
from middleware.auth import get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables are created on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Todo API",
    description="REST API for managing todo items",
    version="2.0.0",
    lifespan=lifespan
)

# --- CORRECTED CORS SETTINGS ---
# CORS origins must not have trailing slashes or sub-paths
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3006",
    "http://localhost:3007",
    "https://shaheryarshah.github.io", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include auth routes
app.include_router(auth_router, prefix="/api/v1")

# Helper functions
def _calculate_overdue(todo: Todo) -> bool:
    if todo.due_date is None or todo.completed:
        return False
    return todo.due_date < datetime.utcnow()

def _todo_to_response(todo: Todo) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        user_id=todo.user_id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        priority=todo.priority,
        tags=todo.tags,
        due_date=todo.due_date,
        recurrence=todo.recurrence,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        overdue=_calculate_overdue(todo)
    )

# --- ROUTES ---

@app.get("/api/v1/todos", response_model=TodoListResponse)
def get_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    due_before: Optional[datetime] = Query(None),
    due_after: Optional[datetime] = Query(None),
    tag: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
):
    service = TodoService(db, user_id=current_user.id)
    todos = service.get_all(search, status, priority, due_before, due_after, tag, sort_by, sort_order)
    return {"todos": [_todo_to_response(t) for t in todos], "count": len(todos), "has_more": False}

@app.post("/api/v1/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo_data: TodoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        service = TodoService(db, user_id=current_user.id)
        return _todo_to_response(service.create(todo_data))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TodoService(db, user_id=current_user.id)
    todo = service.get_by_id(todo_id)
    if not todo: raise HTTPException(status_code=404, detail="Todo not found")
    return _todo_to_response(todo)

@app.put("/api/v1/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_data: TodoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        service = TodoService(db, user_id=current_user.id)
        todo = service.update(todo_id, todo_data)
        if not todo: raise HTTPException(status_code=404, detail="Todo not found")
        return _todo_to_response(todo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TodoService(db, user_id=current_user.id)
    if not service.delete(todo_id): raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
