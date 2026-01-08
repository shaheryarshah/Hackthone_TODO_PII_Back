from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import your database setup and router
from database import init_db  # Adjust if the import path is different
from api.routes.auth import router as auth_router  # Adjust path if needed

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    init_db()
    yield
    # Shutdown: Nothing needed here for now

app = FastAPI(
    title="Todo API",
    description="Backend for TODO Application with Auth and Todos",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware - Fixed for deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # Allows GitHub Pages (any subpath) and localhost
    allow_credentials=True,
    allow_methods=["*"],              # Allows GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include your auth routes (login, register, etc.)
app.include_router(auth_router, prefix="/api/v1")

# Optional: Add a simple root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Todo API is running! 🚀"}

# If you have other routers (e.g., todos), include them here
# from api.routes.todos import router as todos_router
# app.include_router(todos_router, prefix="/api/v1")
