import re
import polars as pl
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from .models import Skill, JobRequirement, SkillLevel


class SkillExtractor:
    """Extracts and matches skills using the existing SkillMiner database."""
    
    def __init__(self, database_path: str = "../database", use_ai_models: bool = False):
        self.db_path = Path(database_path)
        self.use_ai_models = use_ai_models
        self._load_skill_database()
        self._init_skill_patterns()
        
        # Initialize AI models if requested
        if self.use_ai_models:
            self._init_ai_models()
    
    def _load_skill_database(self):
        """Load skills from the existing SkillMiner database."""
        try:
            # Load top skills from gold layer
            top_skills_path = self.db_path / "data" / "gold" / "top_skills.parquet"
            if top_skills_path.exists():
                self.top_skills_df = pl.read_parquet(str(top_skills_path))
                self.known_skills = set(self.top_skills_df["skill"].to_list())
            else:
                self.known_skills = set()
            
            # Load role-specific skills
            role_skills_path = self.db_path / "data" / "gold" / "role_skills_by_title.parquet"
            if role_skills_path.exists():
                self.role_skills_df = pl.read_parquet(str(role_skills_path))
            else:
                self.role_skills_df = None
                
        except Exception as e:
            print(f"Warning: Could not load skill database: {e}")
            self.known_skills = set()
            self.top_skills_df = None
            self.role_skills_df = None
    
    def _init_skill_patterns(self):
        """Initialize common skill patterns and synonyms."""
        # Common programming languages and frameworks
        self.tech_skills = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'spring', 'hibernate', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
            'git', 'jenkins', 'ci/cd', 'agile', 'scrum'
        }
        
        # Data science specific skills
        self.data_skills = {
            'machine learning', 'deep learning', 'data analysis', 'statistics',
            'data visualization', 'etl', 'data mining', 'predictive modeling',
            'a/b testing', 'hypothesis testing', 'regression', 'classification',
            'clustering', 'nlp', 'computer vision', 'time series'
        }
        
        # Combine with database skills
        if self.known_skills:
            self.all_skills = self.known_skills.union(self.tech_skills).union(self.data_skills)
        else:
            self.all_skills = self.tech_skills.union(self.data_skills)
    
    def extract_skills_from_text(self, text: str, context: str = "") -> List[Skill]:
        """Extract skills from text (resume or job description)."""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.all_skills:
            if self._skill_mentioned(skill, text_lower):
                # Try to determine experience level from context
                level = self._extract_skill_level(skill, text_lower)
                years = self._extract_years_experience(skill, text_lower)
                
                found_skills.append(Skill(
                    name=skill,
                    level=level,
                    years_experience=years,
                    context=context
                ))
        
        return found_skills
    
    def extract_job_requirements(self, job_description: str) -> List[JobRequirement]:
        """Extract required skills from job description with importance levels."""
        text_lower = job_description.lower()
        requirements = []
        
        for skill in self.all_skills:
            if self._skill_mentioned(skill, text_lower):
                importance = self._determine_importance(skill, job_description)
                context = self._extract_context(skill, job_description)
                
                requirements.append(JobRequirement(
                    skill=skill,
                    importance=importance,
                    context=context
                ))
        
        return requirements
    
    def _skill_mentioned(self, skill: str, text: str) -> bool:
        """Check if a skill is mentioned in text using various patterns."""
        # Direct match
        if skill in text:
            return True
        
        # Word boundary match for multi-word skills
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
        
        # Handle common variations
        variations = self._get_skill_variations(skill)
        for variation in variations:
            if variation in text:
                return True
        
        return False
    
    def _get_skill_variations(self, skill: str) -> List[str]:
        """Get common variations of a skill name."""
        variations = []
        
        # Common substitutions
        substitutions = {
            'javascript': ['js', 'ecmascript'],
            'typescript': ['ts'],
            'python': ['py'],
            'machine learning': ['ml', 'machinelearning'],
            'artificial intelligence': ['ai'],
            'natural language processing': ['nlp'],
            'node.js': ['nodejs', 'node'],
            'c++': ['cpp', 'c plus plus'],
            'c#': ['csharp', 'c sharp'],
        }
        
        if skill in substitutions:
            variations.extend(substitutions[skill])
        
        return variations
    
    def _extract_skill_level(self, skill: str, text: str) -> Optional[SkillLevel]:
        """Try to extract skill level from context."""
        # Look for level indicators near the skill mention
        skill_pos = text.find(skill.lower())
        if skill_pos == -1:
            return None
        
        # Check surrounding context (±50 characters)
        start = max(0, skill_pos - 50)
        end = min(len(text), skill_pos + len(skill) + 50)
        context = text[start:end]
        
        if any(word in context for word in ['expert', 'advanced', 'senior', 'lead']):
            return SkillLevel.ADVANCED
        elif any(word in context for word in ['intermediate', 'proficient', 'experienced']):
            return SkillLevel.INTERMEDIATE
        elif any(word in context for word in ['beginner', 'basic', 'learning', 'junior']):
            return SkillLevel.BEGINNER
        
        return None
    
    def _extract_years_experience(self, skill: str, text: str) -> Optional[int]:
        """Try to extract years of experience for a skill."""
        skill_pos = text.find(skill.lower())
        if skill_pos == -1:
            return None
        
        # Look for year patterns near the skill
        start = max(0, skill_pos - 100)
        end = min(len(text), skill_pos + len(skill) + 100)
        context = text[start:end]
        
        # Pattern: "X years", "X+ years", "X-Y years"
        year_pattern = r'(\d+)[\+\-\d]*\s*years?'
        matches = re.findall(year_pattern, context, re.IGNORECASE)
        
        if matches:
            return int(matches[0])
        
        return None
    
    def _determine_importance(self, skill: str, job_description: str) -> str:
        """Determine if a skill is required, preferred, or nice-to-have."""
        text_lower = job_description.lower()
        
        # Find the context around the skill mention
        skill_pos = text_lower.find(skill.lower())
        if skill_pos == -1:
            return "nice-to-have"
        
        start = max(0, skill_pos - 100)
        end = min(len(text_lower), skill_pos + len(skill) + 100)
        context = text_lower[start:end]
        
        # Check for requirement indicators
        if any(word in context for word in ['required', 'must have', 'essential', 'mandatory']):
            return "required"
        elif any(word in context for word in ['preferred', 'desired', 'plus', 'bonus']):
            return "preferred"
        else:
            return "nice-to-have"
    
    def _extract_context(self, skill: str, text: str) -> str:
        """Extract the sentence or context where the skill is mentioned."""
        skill_pos = text.lower().find(skill.lower())
        if skill_pos == -1:
            return ""
        
        # Find sentence boundaries
        start = text.rfind('.', 0, skill_pos) + 1
        end = text.find('.', skill_pos + len(skill))
        if end == -1:
            end = len(text)
        
        return text[start:end].strip()
    
    def get_role_specific_skills(self, job_title: str) -> List[str]:
        """Get skills commonly required for a specific role."""
        if self.role_skills_df is None:
            return []
        
        try:
            # Match job title to role in database
            title_lower = job_title.lower()
            
            # Filter for matching roles
            matching_roles = self.role_skills_df.filter(
                pl.col("title_lc").str.contains(title_lower, literal=False)
            )
            
            if matching_roles.height > 0:
                # Get skills for the first matching role
                skills_list = matching_roles.select("skills_list").to_series()[0]
                if skills_list:
                    return skills_list
            
            return []
        except Exception:
            return []   
 
    def _init_ai_models(self):
        """Initialize AI models for enhanced skill extraction."""
        try:
            # Option 1: Use spaCy NER model
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
            
            # Option 2: Use transformers for NER
            # from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
            # self.ner_pipeline = pipeline("ner", 
            #     model="dbmdz/bert-large-cased-finetuned-conll03-english",
            #     aggregation_strategy="simple"
            # )
            
            # Option 3: Use OpenAI API
            # import openai
            # openai.api_key = os.getenv("OPENAI_API_KEY")
            # self.openai_client = openai
            
            # Option 4: Use local LLM (Ollama, etc.)
            # import requests
            # self.llm_endpoint = "http://localhost:11434/api/generate"  # Ollama default
            
        except ImportError as e:
            print(f"Warning: AI model dependencies not available: {e}")
            self.nlp = None
    
    def extract_skills_with_ai(self, text: str, context: str = "") -> List[Skill]:
        """Enhanced skill extraction using AI models."""
        if not self.use_ai_models:
            return self.extract_skills_from_text(text, context)
        
        # Combine rule-based and AI-based extraction
        rule_based_skills = self.extract_skills_from_text(text, context)
        ai_skills = []
        
        # Method 1: spaCy NER
        if hasattr(self, 'nlp') and self.nlp:
            ai_skills.extend(self._extract_with_spacy(text, context))
        
        # Method 2: OpenAI API
        # ai_skills.extend(self._extract_with_openai(text, context))
        
        # Method 3: Local LLM
        # ai_skills.extend(self._extract_with_local_llm(text, context))
        
        # Combine and deduplicate
        all_skills = rule_based_skills + ai_skills
        return self._deduplicate_skills(all_skills)
    
    def _extract_with_spacy(self, text: str, context: str) -> List[Skill]:
        """Extract skills using spaCy NER."""
        skills = []
        doc = self.nlp(text)
        
        # Look for entities that might be skills
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "LANGUAGE"]:  # Potential tech skills
                skill_name = ent.text.lower()
                if skill_name in self.all_skills:
                    skills.append(Skill(
                        name=skill_name,
                        context=f"Detected by NER: {ent.label_}"
                    ))
        
        return skills
    
    def _extract_with_openai(self, text: str, context: str) -> List[Skill]:
        """Extract skills using OpenAI API."""
        try:
            import openai
            import os
            
            if not os.getenv("OPENAI_API_KEY"):
                return []
            
            prompt = f"""
            Extract technical skills from this text. Return only skill names, one per line:
            
            Text: {text[:1000]}  # Limit text length
            
            Skills:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            skills_text = response.choices[0].message.content
            skills = []
            
            for line in skills_text.strip().split('\n'):
                skill_name = line.strip().lower()
                if skill_name and skill_name in self.all_skills:
                    skills.append(Skill(
                        name=skill_name,
                        context="Detected by OpenAI"
                    ))
            
            return skills
            
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            return []
    
    def _extract_with_local_llm(self, text: str, context: str) -> List[Skill]:
        """Extract skills using local LLM (Ollama, etc.)."""
        try:
            import requests
            
            prompt = f"""Extract technical skills from this resume/job text. List only the skill names:

{text[:800]}

Skills:"""
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",  # or "mistral", "codellama", etc.
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                skills_text = result.get("response", "")
                
                skills = []
                for line in skills_text.strip().split('\n'):
                    skill_name = line.strip().lower()
                    # Remove common prefixes/bullets
                    skill_name = skill_name.lstrip('- •*').strip()
                    
                    if skill_name and skill_name in self.all_skills:
                        skills.append(Skill(
                            name=skill_name,
                            context="Detected by Local LLM"
                        ))
                
                return skills
            
        except Exception as e:
            print(f"Local LLM extraction failed: {e}")
            
        return []
    
    def _deduplicate_skills(self, skills: List[Skill]) -> List[Skill]:
        """Remove duplicate skills, keeping the best version."""
        skill_dict = {}
        
        for skill in skills:
            key = skill.name.lower()
            if key not in skill_dict or skill.level or skill.years_experience:
                skill_dict[key] = skill
        
        return list(skill_dict.values())