"""FastAPI application.

Run locally:  uvicorn src.app.api.main:app --reload
Docs:         http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.api.routes import documents
from src.app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="OCR + AraBERT pipeline for Arabic maintenance and safety reports.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
