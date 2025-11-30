from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
import traceback

from src.api.routers import health, chat, upload, analysis, study_plan

app = FastAPI(title="Resume RAG API")

# CORS for your frontend origin(s)
# Note: "*" with allow_credentials=True doesn't work in browsers
# We need to explicitly list origins or use a different approach
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://skillminer.vercel.app/",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Global exception handler for validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


# Global exception handler for unhandled errors (500)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Don't catch HTTPExceptions - let them pass through
    if isinstance(exc, HTTPException):
        raise exc

    print(f"[Global] Unhandled exception: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


app.include_router(health.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(analysis.router)
app.include_router(study_plan.router, prefix="/study-plan", tags=["study-plan"])
