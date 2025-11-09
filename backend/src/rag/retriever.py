import os
from typing import List, Tuple
import chromadb
from chromadb.utils import embedding_functions

from src.core.config import (
    CHROMA_DIR, MODEL_EMBED, TOP_K, MAX_RESUME_CTX, MAX_USER_CTX
)

from pathlib import Path
import pandas as pd
from src.core.config import DATASET_PATH

def _seed_roles_from_parquet(
    dataset_path: Path = DATASET_PATH,
    collection_name: str = "roles_skills",
    batch_size: int = 500,
) -> int:
    """
    Read the roles/skills parquet and upsert into Chroma.
    Expects columns like: role_title, skill, description (adjust below if different).
    """
    if not dataset_path.exists():
        print(f"[RAG] Dataset path does not exist: {dataset_path}")
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    try:
        df = pd.read_parquet(dataset_path)
    except Exception as e:
        print(f"[RAG] Error reading parquet file: {e}")
        raise

    # Ensure we have an 'id' and a 'text' column to index
    if "id" not in df.columns:
        df = df.reset_index(drop=True)
        df["id"] = df.index.astype(str)

    if "text" not in df.columns:
        # Build a text field to embed; handle the actual schema
        # Expected columns: title_lc, skills_for_role (list of skills)
        text_parts = []
        
        # Handle title_lc
        if "title_lc" in df.columns:
            text_parts.append(df["title_lc"].astype(str))
        
        # Handle skills_for_role (list/array of skills)
        if "skills_for_role" in df.columns:
            # Convert list/array to comma-separated string
            def skills_to_str(skills):
                import numpy as np
                if skills is None:
                    return ""
                # Handle numpy arrays
                if isinstance(skills, np.ndarray):
                    skills = skills.tolist()
                # Handle lists
                if isinstance(skills, list):
                    return ", ".join(str(s) for s in skills if s)
                # Handle other types
                return str(skills) if skills else ""
            
            skills_text = df["skills_for_role"].apply(skills_to_str)
            text_parts.append(skills_text)
        
        # Fallback: try other common column names
        if not text_parts:
            for col in ("role_title", "skill", "description"):
                if col in df.columns:
                    text_parts.append(df[col].astype(str))
        
        if text_parts:
            # Combine columns with " | " separator
            df["text"] = text_parts[0]
            for part in text_parts[1:]:
                df["text"] = df["text"] + " | " + part
        else:
            # Fallback: join all columns as strings
            df["text"] = df.astype(str).agg(" ".join, axis=1)
        
        # Truncate text to fit embedding model limits (max ~8000 tokens ≈ 32000 chars)
        # Use a conservative limit to avoid token limit errors
        MAX_TEXT_LENGTH = 30000  # Conservative limit for embedding model
        if df["text"].str.len().max() > MAX_TEXT_LENGTH:
            print(f"[RAG] Warning: Some documents exceed {MAX_TEXT_LENGTH} chars. Truncating...")
            df["text"] = df["text"].str[:MAX_TEXT_LENGTH]

    # Make metadata (everything except id/text)
    # ChromaDB metadata must be simple types (str, int, float, bool, None)
    # Convert arrays/lists to strings
    meta_cols = [c for c in df.columns if c not in ("id", "text")]
    
    def clean_metadata_value(val):
        """Convert metadata values to ChromaDB-compatible types."""
        import numpy as np
        if val is None:
            return None
        # Handle numpy arrays
        if isinstance(val, np.ndarray):
            val = val.tolist()
        # Handle lists
        if isinstance(val, list):
            return ", ".join(str(v) for v in val if v)
        # Handle other types
        return str(val) if not isinstance(val, (str, int, float, bool)) else val
    
    # Clean metadata values
    metadatas = []
    for idx in range(len(df)):
        meta = {}
        for col in meta_cols:
            val = df[col].iloc[idx]
            meta[col] = clean_metadata_value(val)
        metadatas.append(meta)

    col = _get_collection(collection_name)

    # Upsert in batches to avoid huge payloads
    n = len(df)
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        col.upsert(
            ids=df["id"].iloc[start:end].tolist(),
            documents=df["text"].iloc[start:end].tolist(),
            metadatas=metadatas[start:end],
        )
    return col.count()


def ensure_seeded_roles(collection_name: str = "roles_skills") -> int:
    """No-op if already seeded; otherwise seed from parquet."""
    col = _get_collection(collection_name)
    try:
        cnt = col.count()
        if cnt and cnt > 0:
            return cnt
    except Exception:
        pass
    return _seed_roles_from_parquet(collection_name=collection_name)


# If you already maintain your own vector DB elsewhere, replace this with your client.
def _get_collection(name: str = "roles_skills"):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=MODEL_EMBED
    )
    return chroma_client.get_or_create_collection(name=name, embedding_function=openai_ef)



def retrieve(resume_text: str, user_message: str, top_k: int = TOP_K, collection_name: str = "roles_skills"):
    resume_text = resume_text or ""
    user_message = user_message or ""

    try:
        ensure_seeded_roles(collection_name)
    except Exception as e:
        print(f"[RAG] Error seeding roles: {e}")
        # Continue anyway, might work if collection already exists

    # Safely truncate strings
    resume_truncated = resume_text[:MAX_RESUME_CTX] if resume_text else ""
    message_truncated = user_message[:MAX_USER_CTX] if user_message else ""
    
    fused = (
        f"From this resume (truncated): {resume_truncated}\n"
        f"User question: {message_truncated}"
    )
    
    try:
        col = _get_collection(collection_name)
        res = col.query(query_texts=[fused], n_results=top_k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        out = []
        for i, (d, m) in enumerate(zip(docs, metas), start=1):
            # Try multiple possible title fields (prioritize title_lc for this dataset)
            title = ""
            if m:
                title = (m.get("title_lc") or 
                        m.get("title") or 
                        m.get("role_title") or 
                        m.get("skill") or 
                        "")
            header = f"[{i}] {title}".strip() if title else f"[{i}]"
            out.append((header, d))
        return out
    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def build_context_block(resume_text: str, user_message: str, retrieved: List[Tuple[str, str]]) -> str:
    if not retrieved:
        return (
            "CONTEXT: (none retrieved)\n\n"
            f"RESUME (truncated):\n{(resume_text or '')[:MAX_RESUME_CTX]}\n\n"
            f"QUESTION:\n{(user_message or '')[:MAX_USER_CTX]}\n"
        )
    parts = [f"{hdr}\n{doc}" for hdr, doc in retrieved]
    bullets = "\n\n".join(parts)
    return (
        "CONTEXT (use this information naturally in your response, do NOT cite it):\n"
        f"{bullets}\n\n"
        f"RESUME (truncated):\n{(resume_text or '')[:MAX_RESUME_CTX]}\n\n"
        f"QUESTION:\n{(user_message or '')[:MAX_USER_CTX]}\n"
    )
