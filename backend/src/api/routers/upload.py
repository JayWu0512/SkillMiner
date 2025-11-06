from fastapi import APIRouter, UploadFile, File, HTTPException
from src.rag.parser import parse_resume

router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF is supported")
    text = parse_resume(file)
    return {"text": text[:50000]}  # cap for safety
