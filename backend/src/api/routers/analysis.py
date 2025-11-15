# backend/src/api/routers/analysis.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import traceback
import uuid
from datetime import datetime

from src.rag.parser import parse_resume
from src.services.skill_matcher import SkillMatcher
from src.db.supabase_client import get_supabase_client
from src.db.aws_client import get_learning_resources_for_skills

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
    Upload resume PDF + job description, calculate match score and identify skills.
    Returns: analysis_id, user_id, match_score, and skills breakdown.
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
        
        # Calculate match score and identify skills
        try:
            matcher = _get_matcher()
            result = matcher.calculate_match_score(resume_text, job_description)
            
            match_score = result["match_score"]
            matched_technical = result["matched_skills_technical"]
            matched_soft = result["matched_skills_soft"]
            missing_technical = result["missing_skills_technical"]
            missing_soft = result["missing_skills_soft"]
            
            print(f"[Analysis] Score: {match_score}, Matched: {len(matched_technical) + len(matched_soft)}, Missing: {len(missing_technical) + len(missing_soft)}")
            
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
                "matched_skills_technical": matched_technical,
                "matched_skills_soft": matched_soft,
                "missing_skills_technical": missing_technical,
                "missing_skills_soft": missing_soft,
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
            "match_score": round(match_score, 2),
            "matched_skills_technical": matched_technical,
            "matched_skills_soft": matched_soft,
            "missing_skills_technical": missing_technical,
            "missing_skills_soft": missing_soft
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
    Returns: full analysis data including skills breakdown.
    """
    try:
        print(f"[Analysis] Fetching analysis - analysis_id: {analysis_id}")
        
        # Validate analysis_id format
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


@router.get("/analysis/{analysis_id}/resources")
async def get_learning_resources(analysis_id: str, limit_per_skill: int = 3):
    """
    Get learning resources for missing skills in an analysis.
    
    Args:
        analysis_id: The analysis ID
        limit_per_skill: Max resources per skill (default: 3)
    
    Returns:
        {
            "technical": {
                "python": [resources],
                "aws": [resources]
            },
            "soft": {
                "leadership": [resources]
            }
        }
    """
    try:
        print(f"[Resources] Fetching resources for analysis - analysis_id: {analysis_id}")
        
        # Validate analysis_id
        if not analysis_id or not analysis_id.strip():
            raise HTTPException(status_code=400, detail="analysis_id is required")
        
        # Get analysis from Supabase
        try:
            supabase = _get_supabase()
            
            result = supabase.table("skill_analyses")\
                .select("missing_skills_technical, missing_skills_soft")\
                .eq("id", analysis_id)\
                .execute()
            
        except Exception as e:
            print(f"[Resources] Database error fetching analysis: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch analysis: {str(e)}"
            )
        
        # Check if analysis exists
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        analysis = result.data[0]
        missing_technical = analysis.get('missing_skills_technical', [])
        missing_soft = analysis.get('missing_skills_soft', [])
        
        print(f"[Resources] Missing skills - Technical: {len(missing_technical)}, Soft: {len(missing_soft)}")
        
        # Get all missing skills
        all_missing_skills = missing_technical + missing_soft
        
        if not all_missing_skills:
            return {
                "technical": {},
                "soft": {},
                "message": "No missing skills found"
            }
        
        # Query PostgreSQL for learning resources
        try:
            resources_by_skill = get_learning_resources_for_skills(
                all_missing_skills, 
                limit_per_skill=limit_per_skill
            )
        except Exception as e:
            print(f"[Resources] Error fetching learning resources: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch learning resources: {str(e)}"
            )
        
        # Organize by technical/soft
        technical_resources = {}
        soft_resources = {}
        
        for skill in missing_technical:
            skill_lower = skill.lower()
            if skill_lower in resources_by_skill:
                technical_resources[skill] = resources_by_skill[skill_lower]
        
        for skill in missing_soft:
            skill_lower = skill.lower()
            if skill_lower in resources_by_skill:
                soft_resources[skill] = resources_by_skill[skill_lower]
        
        print(f"[Resources] Found resources for {len(technical_resources)} technical and {len(soft_resources)} soft skills")
        
        return {
            "technical": technical_resources,
            "soft": soft_resources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Resources] Unexpected error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )