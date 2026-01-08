from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Local imports
from database import init_db
from api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle events
    """
    # 🔹 Startup
    await init_db()  # make sure init_db is async
    yield
    # 🔹 Shutdown (optional cleanup here)


app = FastAPI(
    title="Todo API",
    description="Backend for TODO Application with Authentication and Todos",
    version="1.0.0",
    lifespan=lifespan,
)

# ✅ CORS Configuration (GitHub Pages + Local Development)
ALLOWED_ORIGINS = [
    "https://shaheryarshah.github.io",
    "https://shaheryarshah.github.io/Hackthone2_TODO_Application_Phase_2",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # ❗ Do NOT use "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 API Routes
app.include_router(auth_router, prefix="/api/v1")

# 🔹 Health Check
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Todo API is running 🚀"}
