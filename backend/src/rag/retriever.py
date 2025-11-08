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
    df = pd.read_parquet(dataset_path)

    # Ensure we have an 'id' and a 'text' column to index
    if "id" not in df.columns:
        df = df.reset_index(drop=True)
        df["id"] = df.index.astype(str)

    if "text" not in df.columns:
        # Build a text field to embed; tailor to your actual schema
        parts = []
        for col in ("role_title", "skill", "description"):
            parts.append(df[col].astype(str) if col in df.columns else "")
        df["text"] = (" | ".join(["{}"] * len(parts))).format(*parts) if parts else df.astype(str).agg(" ".join, axis=1)

    # Make metadata (everything except id/text)
    meta_cols = [c for c in df.columns if c not in ("id", "text")]
    metadatas = df[meta_cols].to_dict(orient="records")

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


    ensure_seeded_roles(collection_name)


    fused = (
        f"From this resume (truncated): {resume_text[:MAX_RESUME_CTX]}\n"
        f"User question: {user_message[:MAX_USER_CTX]}"
    )
    try:
        col = _get_collection(collection_name)
        res = col.query(query_texts=[fused], n_results=top_k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        out = []
        for i, (d, m) in enumerate(zip(docs, metas), start=1):
            title = (m or {}).get("title", "")
            header = f"[{i}] {title}".strip()
            out.append((header, d))
        return out
    except Exception as e:
        print("[RAG] Retrieval error:", e)
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
        "CONTEXT (cite like [1], [2] if used):\n"
        f"{bullets}\n\n"
        f"RESUME (truncated):\n{(resume_text or '')[:MAX_RESUME_CTX]}\n\n"
        f"QUESTION:\n{(user_message or '')[:MAX_USER_CTX]}\n"
    )
