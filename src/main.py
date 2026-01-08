"""FastAPI application for Todo management."""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Path setup
_src_path = Path(__file__).parent
sys.path.insert(0, str(_src_path))
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
    # This ensures tables are created in the database
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Todo API",
    version="2.0.0",
    lifespan=lifespan
)

# --- FIXED CORS CONFIGURATION ---
# IMPORTANT: No trailing slashes, no sub-folders. Just the domain.
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
    expose_headers=["*"], # Helps the browser see error details
)

# Include Auth Router
app.include_router(auth_router, prefix="/api/v1")

# --- TODO ROUTES ---

def _todo_to_response(todo: Todo) -> TodoResponse:
    overdue = False
    if todo.due_date and not todo.completed:
        overdue = todo.due_date < datetime.utcnow()
    
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
        overdue=overdue
    )

@app.get("/api/v1/todos", response_model=TodoListResponse)
def get_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TodoService(db, user_id=current_user.id)
    todos = service.get_all()
    return {"todos": [_todo_to_response(t) for t in todos], "count": len(todos), "has_more": False}

@app.post("/api/v1/todos", response_model=TodoResponse, status_code=201)
def create_todo(
    todo_data: TodoCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    service = TodoService(db, user_id=current_user.id)
    return _todo_to_response(service.create(todo_data))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
