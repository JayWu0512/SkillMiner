from fastapi import APIRouter, UploadFile, File, HTTPException
from src.rag.parser import parse_resume
from src.schemas import UploadResponse
import traceback

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    try:
        print(f"[Upload] Received upload request - filename: {file.filename}, content_type: {file.content_type}")
        # Validate file type
        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type is required")
        
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Validate file size (optional - check if file is too large)
        if hasattr(file, 'size') and file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Parse resume
        try:
            text = parse_resume(file)
        except Exception as e:
            print(f"[Upload] Error parsing PDF: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to parse PDF file: {str(e)}"
            )
        
        # Validate extracted text
        if not text or not text.strip():
            raise HTTPException(
                status_code=400, 
                detail="Could not extract text from PDF. Please ensure the PDF contains readable text."
            )
        
        # Check if parsing returned an error message
        if text.startswith("(Note: could not parse PDF:"):
            raise HTTPException(
                status_code=400,
                detail=text
            )
        
        # Return success response
        return {
            "text": text[:50000],  # cap for safety
            "status": "success",
            "message": "Resume uploaded and parsed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Upload] Unexpected error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )
