# backend/src/api/routers/analysis.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import traceback
import uuid
from datetime import datetime

from src.rag.parser import parse_resume
from src.services.skill_matcher import SkillMatcher
from src.db.supabase_client import get_supabase_client

router = APIRouter()

def _get_supabase():
    """Get Supabase client with error handling."""
    try:
        return get_supabase_client()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Supabase client initialization failed: {str(e)}")

def _get_matcher():
    """Get SkillMatcher with error handling."""
    try:
        return SkillMatcher()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"SkillMatcher initialization failed: {str(e)}")

@router.post("/analysis")
async def create_analysis(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    user_id: str = Form(...)
):
    """
    Upload resume PDF + job description, calculate match score, save to database.
    Returns: analysis_id, user_id, match_score
    """
    try:
        print(f"[Analysis] Received request - filename: {file.filename}, user_id: {user_id}")
        
        # Validate file type
        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type is required")
        
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Validate file size (10MB limit)
        if hasattr(file, 'size') and file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Validate job_description
        if not job_description or not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description is required")
        
        if len(job_description.strip()) < 10:
            raise HTTPException(status_code=400, detail="Job description is too short (minimum 10 characters)")
        
        # Validate user_id
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Parse resume PDF
        try:
            resume_text = parse_resume(file)
        except Exception as e:
            print(f"[Analysis] Error parsing PDF: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse PDF file: {str(e)}"
            )
        
        # Validate extracted text
        if not resume_text or not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. Please ensure the PDF contains readable text."
            )
        
        # Check if parsing returned an error message
        if resume_text.startswith("(Note: could not parse PDF:"):
            raise HTTPException(
                status_code=400,
                detail=resume_text
            )
        
        # Calculate match score with error handling
        try:
            matcher = _get_matcher()
            match_score = matcher.calculate_match_score(resume_text, job_description)
        except Exception as e:
            print(f"[Analysis] Error calculating match score: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate match score: {str(e)}"
            )
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Save to Supabase with error handling
        try:
            supabase = _get_supabase()
            
            result = supabase.table("skill_analyses").insert({
                "id": analysis_id,
                "user_id": user_id,
                "resume_text": resume_text,
                "job_description": job_description,
                "match_score": match_score,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            print(f"[Analysis] Saved to database - analysis_id: {analysis_id}, score: {match_score}")
            
        except Exception as e:
            print(f"[Analysis] Database error: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save analysis to database: {str(e)}"
            )
        
        # Return success response
        return {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "match_score": round(match_score, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analysis] Unexpected error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Get analysis by ID.
    Returns: full analysis data including resume_text, job_description, and match_score.
    """
    try:
        print(f"[Analysis] Fetching analysis - analysis_id: {analysis_id}")
        
        # Validate analysis_id format (basic UUID check)
        if not analysis_id or not analysis_id.strip():
            raise HTTPException(status_code=400, detail="analysis_id is required")
        
        # Get from Supabase with error handling
        try:
            supabase = _get_supabase()
            
            result = supabase.table("skill_analyses")\
                .select("*")\
                .eq("id", analysis_id)\
                .execute()
            
        except Exception as e:
            print(f"[Analysis] Database error: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch analysis from database: {str(e)}"
            )
        
        # Check if analysis exists
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        print(f"[Analysis] Successfully fetched analysis - analysis_id: {analysis_id}")
        
        # Return the analysis data
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analysis] Unexpected error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )