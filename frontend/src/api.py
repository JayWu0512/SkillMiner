from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn
from typing import Optional
import os
from pathlib import Path

from .models import AnalysisRequest, AnalysisResult
from .document_parser import DocumentParser
from .analyzer import SkillGapAnalyzer


# Initialize FastAPI app
app = FastAPI(
    title="SkillMiner Agent",
    description="AI-powered skill gap analysis for job applications",
    version="1.0.0"
)

# Setup static files and templates
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize analyzer
# Set use_ai_models=True to enable AI-powered analysis
USE_AI_MODELS = os.getenv("SKILLMINER_USE_AI", "false").lower() == "true"
analyzer = SkillGapAnalyzer(use_ai_models=USE_AI_MODELS)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main UI page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze_skills(
    job_description: str = Form(...),
    resume_file: Optional[UploadFile] = File(None)
):
    """
    Analyze skill gaps between job description and resume.
    
    Args:
        job_description: The job posting text
        resume_file: Optional PDF or DOCX resume file
    
    Returns:
        AnalysisResult with skill gap analysis
    """
    try:
        # Extract resume text if file provided
        resume_text = None
        if resume_file and resume_file.filename:
            if not resume_file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
                raise HTTPException(
                    status_code=400, 
                    detail="Only PDF and DOCX files are supported"
                )
            
            resume_text = await DocumentParser.extract_text_from_upload(resume_file)
            resume_text = DocumentParser.clean_text(resume_text)
        
        # Create analysis request
        request = AnalysisRequest(
            job_description=job_description,
            resume_text=resume_text
        )
        
        # Perform analysis
        result = analyzer.analyze(request)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze-json", response_model=AnalysisResult)
async def analyze_skills_json(request: AnalysisRequest):
    """
    Analyze skill gaps using JSON input (for API integration).
    
    Args:
        request: AnalysisRequest with job description and optional resume text
    
    Returns:
        AnalysisResult with skill gap analysis
    """
    try:
        result = analyzer.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "SkillMiner Agent"}


@app.get("/api/skills")
async def get_available_skills():
    """Get list of skills in the database."""
    try:
        skills = list(analyzer.skill_extractor.all_skills)
        return {"skills": sorted(skills), "count": len(skills)}
    except Exception as e:
        return {"error": str(e), "skills": [], "count": 0}


@app.get("/api/models")
async def get_model_status():
    """Get status of available AI models."""
    from .model_config import get_available_models, setup_instructions
    
    return {
        "ai_enabled": USE_AI_MODELS,
        "available_models": get_available_models(),
        "setup_instructions": setup_instructions()
    }


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )