"""FastAPI application entry point for the Growup backend."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai.config import load_backend_env
from .routers.diagnostic import router as diagnostic_router

DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


def parse_cors_origins(value: str | None) -> list[str]:
    """Parse a comma-separated origin allow-list without enabling wildcard access."""
    origins = [origin.strip() for origin in (value or "").split(",") if origin.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)


load_backend_env()

app = FastAPI(title="Growup Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(os.getenv("CORS_ORIGINS")),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(diagnostic_router, prefix="/api/ai")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the HTTP application started without reading AI configuration."""
    return {"status": "ok", "service": "growup-backend"}
