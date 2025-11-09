# backend/src/services/skill_matcher.py
import json
from openai import OpenAI
from src.llm.client import get_openai_client
from src.core.config import MODEL_CHAT
from src.rag.retriever import retrieve


class SkillMatcher:
    """Simple service for calculating resume-JD match score."""
    
    client = get_openai_client()
    
    def calculate_match_score(self, resume_text: str, job_description: str) -> float:
        """
        Calculate match score between resume and job description.
        
        Returns:
            float: Match score from 0-100
        """
        # Use RAG to get relevant role context
        try:
            retrieved_roles = retrieve(resume_text, job_description, top_k=3)
            print(retrieved_roles)
            rag_context = "\n".join([doc for _, doc in retrieved_roles[:2]]) if retrieved_roles else ""
            
        except Exception as e:
            print(f"RAG retrieval failed: {e}")
            rag_context = ""
        # Build prompt for LLM
        prompt = f"""Analyze how well this candidate's resume matches the job description. 
                    Provide ONLY a match score from 0-100.

                    Job Description:
                    {job_description[:2000]}

                    Candidate Resume:
                    {resume_text[:2000]}

                    {f"Industry Context: {rag_context[:500]}" if rag_context else ""}

                    Scoring criteria:
                    - 90-100: Excellent match, exceeds requirements
                    - 75-89: Strong match, meets most requirements
                    - 60-74: Good match, some gaps
                    - 40-59: Moderate match, significant gaps
                    - 0-39: Poor match

                    Respond with ONLY a JSON object in this format:
                    {{"match_score": <number between 0 and 100>}}

                    No other text, just the JSON."""
        try:
            response = self.client.chat.completions.create(
                model=MODEL_CHAT,
                temperature=0.2,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise skill matching system. Return only valid JSON with a match_score field."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            # Clean markdown formatting
            content = content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            score = float(result.get("match_score", 0))
            
            # Ensure score is in valid range
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            print(f"Error calculating match score: {e}")
            # Fallback: simple keyword matching
            return self._fallback_score(resume_text, job_description)
    
    def _fallback_score(self, resume_text: str, job_description: str) -> float:
        """Simple fallback scoring if LLM fails."""
        # Extract simple keywords
        jd_words = set(job_description.lower().split())
        resume_words = set(resume_text.lower().split())
        
        # Common tech skills to look for
        common_skills = {
            'python', 'java', 'sql', 'javascript', 'react', 'node', 'aws', 'docker',
            'kubernetes', 'machine learning', 'data', 'analysis', 'api', 'database'
        }
        
        jd_skills = jd_words & common_skills
        resume_skills = resume_words & common_skills
        
        if jd_skills:
            overlap = len(jd_skills & resume_skills)
            score = (overlap / len(jd_skills)) * 100
            return round(score, 1)
        
        return 50.0  # Default neutral score