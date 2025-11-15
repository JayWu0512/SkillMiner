"""
Long-Term Memory (LTM) module for semantic embeddings and NER extraction.
LTM stores semantically meaningful information from previous conversations
in the database for retrieval during inference.
"""
from typing import List, Dict, Optional, Any, Tuple
try:
    import spacy
except ImportError:
    spacy = None
import json
import numpy as np
from datetime import datetime

from src.core.config import LTM_TOP_K, LTM_SIMILARITY_THRESHOLD, NER_MODEL, MODEL_EMBED
from src.llm.client import get_openai_client
from src.db.supabase_client import get_supabase_client


class NERExtractor:
    """Named Entity Recognition extractor using spaCy."""
    
    def __init__(self, model_name: str = NER_MODEL):
        self.model_name = model_name
        self.nlp = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize spaCy NER model."""
        if spacy is None:
            print("[LTM] Warning: spaCy not installed. Install with: pip install spacy")
            self.nlp = None
            return
        
        try:
            self.nlp = spacy.load(self.model_name)
        except OSError:
            print(f"[LTM] Warning: spaCy model '{self.model_name}' not found.")
            print(f"[LTM] Please install it with: python -m spacy download {self.model_name}")
            print("[LTM] Falling back to basic entity extraction")
            # Create a minimal nlp object for fallback
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
        
        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        if not text or not text.strip():
            return {"skills": [], "companies": [], "roles": [], "locations": [], "other": []}
        
        if self.nlp is None:
            # Fallback: basic keyword extraction
            return self._fallback_extraction(text)
        
        try:
            doc = self.nlp(text)
            entities = {
                "skills": [],
                "companies": [],
                "roles": [],
                "locations": [],
                "other": []
            }
            
            # Common tech skills keywords
            tech_skills = [
                "python", "java", "javascript", "typescript", "react", "node.js", "sql",
                "aws", "docker", "kubernetes", "git", "machine learning", "data analysis",
                "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "mongodb",
                "postgresql", "redis", "elasticsearch", "kafka", "graphql", "rest api"
            ]
            
            # Extract entities by type
            for ent in doc.ents:
                entity_text = ent.text.strip().lower()
                
                if ent.label_ in ["ORG", "MONEY"]:
                    # Companies/organizations
                    entities["companies"].append(ent.text)
                elif ent.label_ in ["PERSON"]:
                    # Could be names, but we'll focus on roles
                    pass
                elif ent.label_ in ["GPE", "LOC"]:
                    # Locations
                    entities["locations"].append(ent.text)
                else:
                    entities["other"].append(ent.text)
            
            # Extract skills (check for tech keywords)
            text_lower = text.lower()
            for skill in tech_skills:
                if skill in text_lower:
                    entities["skills"].append(skill.title())
            
            # Extract job roles/titles
            role_keywords = [
                "engineer", "developer", "manager", "analyst", "scientist", "architect",
                "director", "lead", "senior", "junior", "intern", "consultant"
            ]
            for keyword in role_keywords:
                if keyword in text_lower:
                    # Try to extract full role phrase
                    words = text_lower.split()
                    for i, word in enumerate(words):
                        if keyword in word:
                            # Get surrounding context
                            start = max(0, i - 2)
                            end = min(len(words), i + 3)
                            role_phrase = " ".join(words[start:end])
                            entities["roles"].append(role_phrase.title())
                            break
            
            # Remove duplicates
            for key in entities:
                entities[key] = list(set(entities[key]))
            
            return entities
        except Exception as e:
            print(f"[LTM] Error in NER extraction: {e}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text: str) -> Dict[str, List[str]]:
        """Fallback entity extraction using simple keyword matching."""
        text_lower = text.lower()
        entities = {
            "skills": [],
            "companies": [],
            "roles": [],
            "locations": [],
            "other": []
        }
        
        # Basic keyword extraction
        tech_keywords = ["python", "java", "javascript", "sql", "aws", "docker"]
        for keyword in tech_keywords:
            if keyword in text_lower:
                entities["skills"].append(keyword.title())
        
        return entities


class SemanticEmbedder:
    """Semantic embedding extractor using OpenAI."""
    
    def __init__(self):
        self.client = None
        self.model = MODEL_EMBED
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        try:
            self.client = get_openai_client()
        except Exception as e:
            print(f"[LTM] Warning: Could not initialize OpenAI client: {e}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get semantic embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-large) or None
        """
        if not text or not text.strip():
            return None
        
        if self.client is None:
            print("[LTM] Warning: OpenAI client not available, cannot generate embeddings")
            return None
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[LTM] Error generating embedding: {e}")
            return None


class LongTermMemory:
    """
    Long-Term Memory manager for semantic storage and retrieval.
    Stores embeddings and NER entities in Supabase database.
    """
    
    def __init__(self):
        self.ner_extractor = NERExtractor()
        self.embedder = SemanticEmbedder()
        self.supabase = None
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client."""
        try:
            self.supabase = get_supabase_client()
        except Exception as e:
            print(f"[LTM] Warning: Could not initialize Supabase client: {e}")
    
    def store_memory(self, user_id: str, message_id: str, message_content: str) -> Optional[str]:
        """
        Store a message in LTM with embeddings and NER.
        
        Args:
            user_id: User ID
            message_id: Message ID from chat_messages table
            message_content: Message content
        
        Returns:
            LTM entry ID if successful, None otherwise
        """
        if not message_content or not message_content.strip():
            return None
        
        if self.supabase is None:
            print("[LTM] Warning: Supabase not available, cannot store memory")
            return None
        
        try:
            # Extract NER entities
            ner_entities = self.ner_extractor.extract_entities(message_content)
            
            # Get semantic embedding
            embedding = self.embedder.get_embedding(message_content)
            
            if embedding is None:
                print("[LTM] Warning: Could not generate embedding, skipping storage")
                return None
            
            # Store in database
            # pgvector: Store embedding as list, Supabase will convert to vector type
            result = self.supabase.table("chat_ltm_memory").insert({
                "user_id": user_id,
                "message_id": message_id,
                "message_content": message_content,
                "semantic_embedding": embedding,  # List will be converted to vector(1536) by pgvector
                "ner_entities": ner_entities,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            return None
        except Exception as e:
            print(f"[LTM] Error storing memory: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def retrieve_memories(self, user_id: str, query_text: str, top_k: int = LTM_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve relevant LTM entries based on semantic similarity using pgvector.
        
        Args:
            user_id: User ID
            query_text: Query text to find similar memories
            top_k: Number of memories to retrieve
        
        Returns:
            List of LTM entries with similarity scores
        """
        if not query_text or not query_text.strip():
            return []
        
        if self.supabase is None:
            print("[LTM] Warning: Supabase not available, cannot retrieve memories")
            return []
        
        try:
            # Get query embedding
            query_embedding = self.embedder.get_embedding(query_text)
            if query_embedding is None:
                return []
            
            # Use pgvector similarity search via RPC function
            # First, try using a PostgreSQL function for vector similarity
            try:
                # Call RPC function for vector similarity search
                # Note: This requires creating a function in Supabase (see migration file)
                result = self.supabase.rpc(
                    "match_ltm_memories",
                    {
                        "query_embedding": query_embedding,
                        "match_user_id": user_id,
                        "match_threshold": LTM_SIMILARITY_THRESHOLD,
                        "match_count": top_k
                    }
                ).execute()
                
                if result.data:
                    return result.data
            except Exception as rpc_error:
                # Fallback to Python-based similarity if RPC function doesn't exist
                print(f"[LTM] RPC function not available, using Python similarity: {rpc_error}")
                return self._retrieve_memories_python(user_id, query_embedding, top_k)
            
            # If RPC returned no data, fallback to Python
            return self._retrieve_memories_python(user_id, query_embedding, top_k)
        
        except Exception as e:
            print(f"[LTM] Error retrieving memories: {e}")
            import traceback
            print(traceback.format_exc())
            # Try to get embedding for fallback
            try:
                query_embedding = self.embedder.get_embedding(query_text)
                if query_embedding:
                    return self._retrieve_memories_python(user_id, query_embedding, top_k)
            except:
                pass
            return []
    
    def _retrieve_memories_python(self, user_id: str, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        Fallback: Retrieve memories using Python-based cosine similarity computation.
        
        Args:
            user_id: User ID
            query_embedding: Query embedding vector
            top_k: Number of memories to retrieve
        
        Returns:
            List of LTM entries with similarity scores
        """
        try:
            # Get all LTM entries for user
            # Get more than top_k to compute similarities
            result = self.supabase.table("chat_ltm_memory")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            if not result.data:
                return []
            
            # Compute cosine similarities
            memories_with_scores = []
            query_vec = np.array(query_embedding)
            query_norm = np.linalg.norm(query_vec)
            
            for entry in result.data:
                stored_embedding = entry.get("semantic_embedding")
                if stored_embedding:
                    # Handle both vector type (from pgvector) and JSONB formats
                    if isinstance(stored_embedding, str):
                        stored_embedding = json.loads(stored_embedding)
                    elif isinstance(stored_embedding, list):
                        pass  # Already a list
                    else:
                        # Vector type might be returned as array-like
                        stored_embedding = list(stored_embedding) if hasattr(stored_embedding, '__iter__') else []
                    
                    if len(stored_embedding) > 0:
                        stored_vec = np.array(stored_embedding)
                        stored_norm = np.linalg.norm(stored_vec)
                        
                        if stored_norm > 0 and query_norm > 0:
                            similarity = np.dot(query_vec, stored_vec) / (query_norm * stored_norm)
                            
                            if similarity >= LTM_SIMILARITY_THRESHOLD:
                                memories_with_scores.append({
                                    "id": entry["id"],
                                    "message_id": entry.get("message_id"),
                                    "message_content": entry.get("message_content"),
                                    "ner_entities": entry.get("ner_entities", {}),
                                    "similarity": float(similarity),
                                    "created_at": entry.get("created_at")
                                })
            
            # Sort by similarity and return top_k
            memories_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
            return memories_with_scores[:top_k]
        
        except Exception as e:
            print(f"[LTM] Error in Python similarity computation: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_ltm_summary(self, memories: List[Dict[str, Any]]) -> str:
        """
        Generate a summary from retrieved LTM memories.
        
        Args:
            memories: List of LTM memory entries
        
        Returns:
            Formatted summary string
        """
        if not memories:
            return ""
        
        summary_parts = []
        
        # Extract key information from memories
        all_entities = {
            "skills": set(),
            "companies": set(),
            "roles": set(),
            "locations": set()
        }
        
        relevant_content = []
        
        for memory in memories:
            # Collect entities
            ner_entities = memory.get("ner_entities", {})
            for entity_type in all_entities:
                if entity_type in ner_entities:
                    all_entities[entity_type].update(ner_entities[entity_type])
            
            # Collect relevant content snippets
            content = memory.get("message_content", "")
            if content:
                # Truncate long content
                if len(content) > 200:
                    content = content[:200] + "..."
                relevant_content.append(content)
        
        # Build summary
        if all_entities["skills"]:
            summary_parts.append(f"Skills mentioned: {', '.join(list(all_entities['skills'])[:10])}")
        
        if all_entities["roles"]:
            summary_parts.append(f"Roles discussed: {', '.join(list(all_entities['roles'])[:5])}")
        
        if all_entities["companies"]:
            summary_parts.append(f"Companies mentioned: {', '.join(list(all_entities['companies'])[:5])}")
        
        if relevant_content:
            summary_parts.append(f"Relevant context: {' | '.join(relevant_content[:3])}")
        
        return "\n".join(summary_parts) if summary_parts else ""


# Global LTM instance
_ltm_instance: Optional[LongTermMemory] = None


def get_ltm() -> LongTermMemory:
    """Get or create global LTM instance."""
    global _ltm_instance
    if _ltm_instance is None:
        _ltm_instance = LongTermMemory()
    return _ltm_instance

