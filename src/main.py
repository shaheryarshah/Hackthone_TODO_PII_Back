from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base, init_db
from api.routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This automatically creates your User and Todo tables in the database
    init_db()
    yield

app = FastAPI(title="Todo API", lifespan=lifespan)

# FIX: No trailing slashes, no sub-folders in origins
origins = [
    "http://localhost:3000",
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

app.include_router(auth_router, prefix="/api/v1")
