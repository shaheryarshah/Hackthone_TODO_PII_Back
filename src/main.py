from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import your database setup and router
from database import init_db
from api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (nothing needed)


app = FastAPI(
    title="Todo API",
    description="Backend for TODO Application with Auth and Todos",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ FIXED CORS CONFIG (GitHub Pages + Localhost)
origins = [
    "https://shaheryarshah.github.io",
    "https://shaheryarshah.github.io/Hackthone2_TODO_Application_Phase_2",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # ❗ NO "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Todo API is running! 🚀"}
