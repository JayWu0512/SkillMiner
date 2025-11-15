# backend/src/services/skill_matcher.py
import json
from typing import Dict, List
from openai import OpenAI
from src.llm.client import get_openai_client
from src.core.config import MODEL_CHAT
from src.rag.retriever import retrieve
from src.db.aws_client import get_skills_by_names


class SkillMatcher:
    """Service for calculating resume-JD match score and identifying skills."""
    
    def __init__(self):
        self.client: OpenAI = get_openai_client()
    
    def calculate_match_score(self, resume_text: str, job_description: str) -> Dict:
        """
        Calculate match score and identify skills.
        
        Returns:
            Dict with:
            - match_score: float (0-100)
            - matched_skills_technical: List[str]
            - matched_skills_soft: List[str]
            - missing_skills_technical: List[str]
            - missing_skills_soft: List[str]
        """
        # Use RAG to get relevant role context
        try:
            retrieved_roles = retrieve(resume_text, job_description, top_k=5)
            rag_context = "\n".join([doc for _, doc in retrieved_roles[:2]]) if retrieved_roles else ""
            print(f"[SkillMatcher] RAG context retrieved")
        except Exception as e:
            print(f"[SkillMatcher] RAG retrieval failed: {e}")
            rag_context = ""
        
        # Extract skills from JD and resume using LLM
        jd_skills = self._extract_skills_from_text(job_description, "job description")
        resume_skills = self._extract_skills_from_text(resume_text, "resume")
        
        print(f"[SkillMatcher] Extracted {len(jd_skills)} skills from JD, {len(resume_skills)} from resume")
        
        # Combine all unique skills mentioned
        all_mentioned_skills = list(set(jd_skills + resume_skills))
        
        # Query database to get validated skills with their types
        db_skills = get_skills_by_names(all_mentioned_skills)
        
        # Create lookup dict: skill_name -> skill_type
        skill_type_map = {
            skill['skill_name'].lower(): skill['skill_type'] 
            for skill in db_skills
        }
        
        print(f"[SkillMatcher] Found {len(db_skills)} skills in database")
        
        # Categorize matched and missing skills
        matched_technical = []
        matched_soft = []
        missing_technical = []
        missing_soft = []
        
        for jd_skill in jd_skills:
            skill_lower = jd_skill.lower()
            
            # Check if skill is in database
            if skill_lower not in skill_type_map:
                continue  # Skip skills not in database
            
            skill_type = skill_type_map[skill_lower]
            
            # Check if candidate has this skill
            if skill_lower in [s.lower() for s in resume_skills]:
                # Matched skill
                if skill_type == 'technical':
                    matched_technical.append(jd_skill)
                else:  # soft
                    matched_soft.append(jd_skill)
            else:
                # Missing skill
                if skill_type == 'technical':
                    missing_technical.append(jd_skill)
                else:  # soft
                    missing_soft.append(jd_skill)
        
        # Calculate match score using LLM
        match_score = self._calculate_score_with_llm(
            resume_text, 
            job_description, 
            rag_context,
            matched_technical,
            matched_soft,
            missing_technical,
            missing_soft
        )
        
        return {
            "match_score": match_score,
            "matched_skills_technical": matched_technical,
            "matched_skills_soft": matched_soft,
            "missing_skills_technical": missing_technical,
            "missing_skills_soft": missing_soft
        }
    
    def _extract_skills_from_text(self, text: str, text_type: str) -> List[str]:
        """Extract skills from text using LLM."""
        prompt = f"""Extract all skills mentioned in this {text_type}.
Include technical skills, soft skills, tools, technologies, and qualifications.

Text:
{text[:2000]}

Return ONLY a JSON array of skill names, nothing else.
Example: ["Python", "Communication", "Leadership", "SQL"]

Be comprehensive but precise. Return actual skills mentioned, not inferred ones."""

        try:
            response = self.client.chat.completions.create(
                model=MODEL_CHAT,
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill extraction expert. Return only valid JSON arrays."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            content = content.replace("```json", "").replace("```", "").strip()
            
            skills = json.loads(content)
            return skills if isinstance(skills, list) else []
            
        except Exception as e:
            print(f"[SkillMatcher] Error extracting skills from {text_type}: {e}")
            return []
    
    def _calculate_score_with_llm(
        self, 
        resume_text: str, 
        job_description: str,
        rag_context: str,
        matched_technical: List[str],
        matched_soft: List[str],
        missing_technical: List[str],
        missing_soft: List[str]
    ) -> float:
        """Calculate match score using LLM with skill context."""
        
        prompt = f"""Analyze how well this candidate matches the job requirements.

Job Description:
{job_description[:1500]}

Candidate Resume:
{resume_text[:1500]}

Industry Context:
{rag_context[:500] if rag_context else "N/A"}

Skill Analysis:
- Matched Technical Skills ({len(matched_technical)}): {', '.join(matched_technical[:10])}
- Matched Soft Skills ({len(matched_soft)}): {', '.join(matched_soft[:10])}
- Missing Technical Skills ({len(missing_technical)}): {', '.join(missing_technical[:10])}
- Missing Soft Skills ({len(missing_soft)}): {', '.join(missing_soft[:10])}

Provide a match score from 0-100 considering:
- Technical skill coverage
- Soft skill alignment
- Experience relevance
- Overall qualification level

Scoring criteria:
- 90-100: Excellent match, exceeds requirements
- 75-89: Strong match, meets most requirements
- 60-74: Good match, some gaps
- 40-59: Moderate match, significant gaps
- 0-39: Poor match

Return ONLY a JSON object: {{"match_score": <number>}}"""

        try:
            response = self.client.chat.completions.create(
                model=MODEL_CHAT,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise skill matching system. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            content = content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            score = float(result.get("match_score", 0))
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            print(f"[SkillMatcher] Error calculating score: {e}")
            # Fallback: simple calculation based on skill matches
            total_required = len(matched_technical) + len(matched_soft) + len(missing_technical) + len(missing_soft)
            total_matched = len(matched_technical) + len(matched_soft)
            
            if total_required > 0:
                score = (total_matched / total_required) * 100
                return round(score, 1)
            
            return 50.0