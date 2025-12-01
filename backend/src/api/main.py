# src/main.py  或 app.py

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
# CORS 設定
# -----------------------------
# 這裡先把「本機開發」和「正式前端」的 domain 都列進來
ALLOWED_ORIGINS = [
    # 正式前端（Vercel）
    "https://skillminer.vercel.app",
    # 本機開發
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# 如果之後想在 Railway 上動態加其他 origin，可以設環境變數 CORS_EXTRA_ORIGINS
# 例如：CORS_EXTRA_ORIGINS="https://another-frontend.com,https://foo.bar"
extra_origins = os.getenv("CORS_EXTRA_ORIGINS")
if extra_origins:
    ALLOWED_ORIGINS.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

logger.info(f"[CORS] Allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # 只要是標準 REST 動作就都放行
    allow_headers=["*"],
    expose_headers=["*"],
)

# -----------------------------
# 基本健康檢查 & root
# -----------------------------


@app.get("/", tags=["meta"])
async def root():
    """簡單回報後端有在跑，方便在瀏覽器 /health 之外再測一個 endpoint。"""
    return {"status": "ok", "service": "skillminer-backend"}


# -----------------------------
# 全域錯誤處理
# -----------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """pydantic 驗證錯誤（422）統一格式"""
    logger.warning(f"[ValidationError] path={request.url.path} errors={exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """未預期錯誤（500）統一處理 & log"""
    if isinstance(exc, HTTPException):
        # 讓 FastAPI 原本的 HTTPException handler 處理（例如 raise HTTPException(404)）
        raise exc

    logger.error(f"[Global] Unhandled exception at {request.url.path}: {exc}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# -----------------------------
# 路由註冊
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
