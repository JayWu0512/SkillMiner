from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's latest message")
    resume_text: Optional[str] = Field(None, description="Optional resume text you already extracted")

class ChatResponse(BaseModel):
    reply: str
    citations: List[str] = []
