"""
Script-to-Screen Guardian — FastAPI entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.routes.api import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])

app = FastAPI(
    title="Script-to-Screen Guardian",
    description="Multi-agent AI system that predicts and prevents film production disruptions.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/")
async def root():
    return {
        "name": "Script-to-Screen Guardian",
        "docs": "/docs",
        "health": "/health",
    }
