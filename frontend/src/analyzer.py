import re
from typing import List, Dict, Set
from .models import (
    AnalysisResult, Skill, JobRequirement, SkillGap, 
    AnalysisRequest, SkillLevel
)
from .skill_extractor import SkillExtractor


class SkillGapAnalyzer:
    """Analyzes skill gaps between job requirements and resume skills."""
    
    def __init__(self, database_path: str = "../database", use_ai_models: bool = False):
        self.skill_extractor = SkillExtractor(database_path, use_ai_models)
        self.use_ai_models = use_ai_models
    
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform complete skill gap analysis."""
        
        # Extract job title from description
        job_title = self._extract_job_title(request.job_description)
        
        # Extract required skills from job description
        required_skills = self.skill_extractor.extract_job_requirements(
            request.job_description
        )
        
        # Extract existing skills from resume
        existing_skills = []
        if request.resume_text:
            if self.use_ai_models:
                existing_skills = self.skill_extractor.extract_skills_with_ai(
                    request.resume_text, "resume"
                )
            else:
                existing_skills = self.skill_extractor.extract_skills_from_text(
                    request.resume_text, "resume"
                )
        
        # Identify missing skills and gaps
        missing_skills, skill_gaps = self._analyze_gaps(
            required_skills, existing_skills
        )
        
        # Calculate match score
        match_score = self._calculate_match_score(
            required_skills, existing_skills
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            skill_gaps, job_title
        )
        
        # Create summary
        summary = self._create_summary(
            match_score, len(required_skills), len(existing_skills), 
            len(missing_skills)
        )
        
        return AnalysisResult(
            job_title=job_title,
            required_skills=required_skills,
            existing_skills=existing_skills,
            missing_skills=missing_skills,
            skill_gaps=skill_gaps,
            match_score=match_score,
            recommendations=recommendations,
            summary=summary
        )
    
    def _extract_job_title(self, job_description: str) -> str:
        """Extract job title from job description."""
        lines = job_description.split('\n')
        
        # Look for common title patterns in first few lines
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
                
            # Skip if line is too long (likely not a title)
            if len(line) > 100:
                continue
                
            # Common title indicators
            title_indicators = [
                'position:', 'role:', 'job title:', 'title:',
                'we are looking for', 'seeking', 'hiring'
            ]
            
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in title_indicators):
                # Extract title after indicator
                for indicator in title_indicators:
                    if indicator in line_lower:
                        title = line_lower.split(indicator, 1)[1].strip()
                        return title.title()
            
            # If line contains common job words, it might be a title
            job_words = [
                'engineer', 'developer', 'analyst', 'scientist', 
                'manager', 'lead', 'senior', 'junior'
            ]
            if any(word in line_lower for word in job_words):
                return line.title()
        
        return "Unknown Position"
    
    def _analyze_gaps(
        self, 
        required_skills: List[JobRequirement], 
        existing_skills: List[Skill]
    ) -> tuple[List[str], List[SkillGap]]:
        """Analyze gaps between required and existing skills."""
        
        existing_skill_names = {skill.name.lower() for skill in existing_skills}
        existing_skills_dict = {skill.name.lower(): skill for skill in existing_skills}
        
        missing_skills = []
        skill_gaps = []
        
        for req in required_skills:
            req_skill_lower = req.skill.lower()
            
            if req_skill_lower not in existing_skill_names:
                # Completely missing skill
                missing_skills.append(req.skill)
                
                gap_severity = self._determine_gap_severity(req.importance)
                recommendations = self._get_skill_recommendations(req.skill, req.importance)
                
                skill_gaps.append(SkillGap(
                    skill=req.skill,
                    required_level=req.importance,
                    current_level="none",
                    gap_severity=gap_severity,
                    recommendations=recommendations
                ))
            else:
                # Skill exists, check level gap
                existing_skill = existing_skills_dict[req_skill_lower]
                gap = self._assess_skill_level_gap(req, existing_skill)
                
                if gap:
                    skill_gaps.append(gap)
        
        return missing_skills, skill_gaps
    
    def _determine_gap_severity(self, importance: str) -> str:
        """Determine gap severity based on skill importance."""
        if importance == "required":
            return "critical"
        elif importance == "preferred":
            return "moderate"
        else:
            return "minor"
    
    def _assess_skill_level_gap(
        self, 
        requirement: JobRequirement, 
        existing_skill: Skill
    ) -> SkillGap:
        """Assess if there's a level gap for an existing skill."""
        
        # If we can't determine levels, assume it's adequate
        if not existing_skill.level:
            return None
        
        # Define level hierarchy
        level_hierarchy = {
            SkillLevel.BEGINNER: 1,
            SkillLevel.INTERMEDIATE: 2,
            SkillLevel.ADVANCED: 3,
            SkillLevel.EXPERT: 4
        }
        
        # Estimate required level based on importance and context
        required_level = self._estimate_required_level(requirement)
        
        if required_level and existing_skill.level:
            current_level_score = level_hierarchy.get(existing_skill.level, 1)
            required_level_score = level_hierarchy.get(required_level, 2)
            
            if current_level_score < required_level_score:
                gap_severity = "moderate" if requirement.importance == "required" else "minor"
                recommendations = self._get_level_improvement_recommendations(
                    requirement.skill, existing_skill.level, required_level
                )
                
                return SkillGap(
                    skill=requirement.skill,
                    required_level=required_level.value,
                    current_level=existing_skill.level.value,
                    gap_severity=gap_severity,
                    recommendations=recommendations
                )
        
        return None
    
    def _estimate_required_level(self, requirement: JobRequirement) -> SkillLevel:
        """Estimate required skill level from job requirement context."""
        context_lower = requirement.context.lower()
        
        if any(word in context_lower for word in ['expert', 'advanced', 'senior', 'lead']):
            return SkillLevel.ADVANCED
        elif any(word in context_lower for word in ['proficient', 'experienced', 'solid']):
            return SkillLevel.INTERMEDIATE
        elif requirement.importance == "required":
            return SkillLevel.INTERMEDIATE
        else:
            return SkillLevel.BEGINNER
    
    def _calculate_match_score(
        self, 
        required_skills: List[JobRequirement], 
        existing_skills: List[Skill]
    ) -> float:
        """Calculate overall match score (0-100)."""
        
        if not required_skills:
            return 100.0
        
        existing_skill_names = {skill.name.lower() for skill in existing_skills}
        
        total_weight = 0
        matched_weight = 0
        
        for req in required_skills:
            # Weight skills by importance
            weight = 3 if req.importance == "required" else 2 if req.importance == "preferred" else 1
            total_weight += weight
            
            if req.skill.lower() in existing_skill_names:
                matched_weight += weight
        
        if total_weight == 0:
            return 100.0
        
        return (matched_weight / total_weight) * 100
    
    def _get_skill_recommendations(self, skill: str, importance: str) -> List[str]:
        """Get learning recommendations for a missing skill."""
        recommendations = []
        
        # Skill-specific recommendations
        skill_lower = skill.lower()
        
        if skill_lower in ['python', 'java', 'javascript', 'typescript']:
            recommendations.extend([
                f"Complete an online {skill} course (Coursera, Udemy, or Codecademy)",
                f"Build 2-3 projects using {skill} to demonstrate proficiency",
                f"Contribute to open-source {skill} projects on GitHub"
            ])
        elif skill_lower in ['machine learning', 'deep learning']:
            recommendations.extend([
                "Take Andrew Ng's Machine Learning course on Coursera",
                "Complete Kaggle competitions to build practical experience",
                "Build and deploy ML models using popular frameworks"
            ])
        elif skill_lower in ['sql', 'postgresql', 'mysql']:
            recommendations.extend([
                "Practice SQL queries on platforms like HackerRank or LeetCode",
                "Work with real datasets to build database skills",
                "Learn database design and optimization techniques"
            ])
        elif skill_lower in ['docker', 'kubernetes']:
            recommendations.extend([
                "Complete Docker/Kubernetes tutorials and certifications",
                "Containerize existing projects",
                "Deploy applications using container orchestration"
            ])
        else:
            recommendations.extend([
                f"Take an online course or tutorial on {skill}",
                f"Practice {skill} through hands-on projects",
                f"Join communities and forums focused on {skill}"
            ])
        
        # Add urgency based on importance
        if importance == "required":
            recommendations.insert(0, f"Priority: {skill} is required - focus on this skill first")
        
        return recommendations
    
    def _get_level_improvement_recommendations(
        self, 
        skill: str, 
        current_level: SkillLevel, 
        required_level: SkillLevel
    ) -> List[str]:
        """Get recommendations for improving skill level."""
        return [
            f"Advance your {skill} skills from {current_level.value} to {required_level.value} level",
            f"Take advanced {skill} courses or certifications",
            f"Work on more complex {skill} projects",
            f"Seek mentorship or pair programming opportunities in {skill}"
        ]
    
    def _generate_recommendations(
        self, 
        skill_gaps: List[SkillGap], 
        job_title: str
    ) -> List[str]:
        """Generate overall recommendations for the candidate."""
        recommendations = []
        
        # Priority recommendations based on critical gaps
        critical_gaps = [gap for gap in skill_gaps if gap.gap_severity == "critical"]
        if critical_gaps:
            recommendations.append(
                f"Focus immediately on these critical skills: {', '.join([gap.skill for gap in critical_gaps[:3]])}"
            )
        
        # Role-specific advice
        if job_title and "data" in job_title.lower():
            recommendations.append(
                "Build a portfolio showcasing data analysis and visualization projects"
            )
        elif job_title and "engineer" in job_title.lower():
            recommendations.append(
                "Create a GitHub portfolio with well-documented code projects"
            )
        
        # General advice
        if len(skill_gaps) > 5:
            recommendations.append(
                "Consider taking a comprehensive bootcamp or course to address multiple skill gaps efficiently"
            )
        
        recommendations.extend([
            "Update your resume to highlight relevant projects and experiences",
            "Practice technical interviews focusing on the required skills",
            "Network with professionals in the target role through LinkedIn and industry events"
        ])
        
        return recommendations
    
    def _create_summary(
        self, 
        match_score: float, 
        total_required: int, 
        total_existing: int, 
        total_missing: int
    ) -> str:
        """Create a summary of the analysis."""
        
        if match_score >= 80:
            fit_level = "excellent"
        elif match_score >= 60:
            fit_level = "good"
        elif match_score >= 40:
            fit_level = "moderate"
        else:
            fit_level = "poor"
        
        summary = f"Overall match score: {match_score:.1f}% ({fit_level} fit). "
        summary += f"You have {total_existing} relevant skills and are missing {total_missing} "
        summary += f"out of {total_required} required skills. "
        
        if total_missing == 0:
            summary += "Congratulations! You meet all the skill requirements."
        elif total_missing <= 3:
            summary += "With some focused learning, you could be a strong candidate."
        else:
            summary += "Consider developing the missing skills before applying."
        
        return summary