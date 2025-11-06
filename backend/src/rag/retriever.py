import os
from typing import List, Tuple
import chromadb
from chromadb.utils import embedding_functions

from src.core.config import (
    CHROMA_DIR, MODEL_EMBED, TOP_K, MAX_RESUME_CTX, MAX_USER_CTX
)

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
