"""Điểm khởi chạy API Growup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.config import get_settings
from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.diagnostic import router as diagnostic_router
from app.routers.diagnostic_sessions import router as diagnostic_sessions_router
from app.routers.classifications import router as classifications_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(auth_router)
app.include_router(diagnostic_router, prefix="/api/ai")
app.include_router(diagnostic_sessions_router, prefix="/api")
app.include_router(classifications_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
