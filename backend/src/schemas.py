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
