from pydantic import BaseModel, Field, validator
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's latest message", min_length=1)
    resume_text: Optional[str] = Field(None, description="Optional resume text you already extracted")
    user_id: Optional[str] = Field(None, description="Optional user ID for memory-augmented context retention")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

class ChatResponse(BaseModel):
    reply: str
    citations: List[str] = []

class UploadResponse(BaseModel):
    text: str
    status: str = "success"
    message: str = "Resume uploaded and parsed successfully"

class AnalysisRequest(BaseModel):
    """Request model for skill gap analysis."""
    resume_text: str = Field(..., description="Resume text", min_length=10)
    job_description: str = Field(..., description="Job description text", min_length=10)
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    
    @validator('resume_text', 'job_description')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

class AnalysisResponse(BaseModel):
    """Response model for skill gap analysis."""
    analysis_id: str = Field(..., description="Unique ID for this analysis")
    match_score: float = Field(..., description="Match score (0-100)", ge=0, le=100)
    message: str = Field(default="Analysis completed successfully")

class StudyPlanUpdateRequest(BaseModel):
    """Request model for study plan updates."""
    user_id: str = Field(..., description="User ID to find and update the study plan")
    action: str = Field(..., description="Action type: reduce_hours, increase_hours, extend_timeline, shorten_timeline, add_rest_days, reduce_rest_days")
    params: dict = Field(..., description="Update parameters (e.g., {'hoursPerDay': '2-3', 'additionalDays': 14})")

class StudyPlanUpdateResponse(BaseModel):
    """Response model for study plan updates."""
    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Status message")
    plan_id: str = Field(..., description="Updated study plan ID")

