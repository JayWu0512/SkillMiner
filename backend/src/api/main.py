from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import health, chat, upload

app = FastAPI(title="Resume RAG API")

# CORS for your frontend origin(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(chat.router)
