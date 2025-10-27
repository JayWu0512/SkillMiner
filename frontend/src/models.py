from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    name: str
    level: Optional[SkillLevel] = None
    years_experience: Optional[int] = None
    context: Optional[str] = None  # Where it was mentioned in resume


class JobRequirement(BaseModel):
    skill: str
    importance: str  # required, preferred, nice-to-have
    context: str  # Where mentioned in job description


class SkillGap(BaseModel):
    skill: str
    required_level: Optional[str] = None
    current_level: Optional[str] = None
    gap_severity: str  # critical, moderate, minor
    recommendations: List[str]


class AnalysisRequest(BaseModel):
    job_description: str
    resume_text: Optional[str] = None  # Will be extracted from uploaded file


class AnalysisResult(BaseModel):
    job_title: Optional[str] = None
    required_skills: List[JobRequirement]
    existing_skills: List[Skill]
    missing_skills: List[str]
    skill_gaps: List[SkillGap]
    match_score: float  # 0-100 percentage
    recommendations: List[str]
    summary: str