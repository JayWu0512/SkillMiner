# src/main.py or app.py

import os
import traceback
import logging

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from src.api.routers import health, chat, upload, analysis, study_plan

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="SkillMiner API")

# -----------------------------
# CORS Configuration
# -----------------------------
# List both local development and production frontend domains here
ALLOWED_ORIGINS = [
    # Production frontend (Vercel)
    "https://skillminer.vercel.app",
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# If you want to dynamically add other origins on Railway later, you can set the CORS_EXTRA_ORIGINS environment variable
# Example: CORS_EXTRA_ORIGINS="https://another-frontend.com,https://foo.bar"
extra_origins = os.getenv("CORS_EXTRA_ORIGINS")
if extra_origins:
    ALLOWED_ORIGINS.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

logger.info(f"[CORS] Allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all standard REST actions
    allow_headers=["*"],
    expose_headers=["*"],
)

# -----------------------------
# Basic health check & root
# -----------------------------


@app.get("/", tags=["meta"])
async def root():
    """Simple endpoint to report that the backend is running, convenient for testing another endpoint besides /health in the browser."""
    return {"status": "ok", "service": "skillminer-backend"}


# -----------------------------
# Global error handling
# -----------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Unified format for pydantic validation errors (422)"""
    logger.warning(f"[ValidationError] path={request.url.path} errors={exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Unified handling & logging for unexpected errors (500)"""
    if isinstance(exc, HTTPException):
        # Let FastAPI's default HTTPException handler process it (e.g., raise HTTPException(404))
        raise exc

    logger.error(f"[Global] Unhandled exception at {request.url.path}: {exc}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# -----------------------------
# Route registration
# -----------------------------

app.include_router(health.router)  # /health
app.include_router(upload.router)  # /upload
app.include_router(chat.router)  # /chat
app.include_router(analysis.router)  # /analysis
app.include_router(
    study_plan.router,
    prefix="/study-plan",
    tags=["study-plan"],
)
