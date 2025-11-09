from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's latest message", min_length=1)
    resume_text: Optional[str] = Field(None, description="Optional resume text you already extracted")
    
    @field_validator('message')
    @classmethod
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
    
    @field_validator('resume_text', 'job_description')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

class AnalysisResponse(BaseModel):
    """Response model for skill gap analysis."""
    analysis_id: str = Field(..., description="Unique ID for this analysis")
    match_score: float = Field(..., description="Match score (0-100)", ge=0, le=100)
    message: str = Field(default="Analysis completed successfully")

