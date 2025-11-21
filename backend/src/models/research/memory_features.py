# models/research/memory_features.py
from typing import List, Dict, Any
import numpy as np

from models.stm import SummarizationLayer, TokenLimitController
from models.ltm import NERExtractor, SemanticEmbedder


class SummarizationFeature:
    def __init__(self):
        self.summarizer = SummarizationLayer()

    def summarize(self, text: str) -> str:
        return self.summarizer.summarize(text)


class TokenLimitFeature:
    def __init__(self, max_tokens: int):
        self.controller = TokenLimitController(max_tokens)

    def truncate(self, text: str) -> str:
        return self.controller.truncate(text)


class NERFeature:
    def __init__(self):
        self.ner = NERExtractor()

    def extract(self, text: str) -> Dict[str, list]:
        return self.ner.extract_entities(text)


class LocalSemanticMemory:
    """Simplified LTM: stored only in memory, does not use Supabase."""

    def __init__(self):
        self.embedder = SemanticEmbedder()
        self.entries: List[Dict[str, Any]] = []

    def add(self, text: str):
        emb = self.embedder.get_embedding(text)
        if not emb:
            return
        self.entries.append({"text": text, "embedding": np.array(emb)})

    def search(self, query: str, top_k: int = 5) -> List[str]:
        emb = self.embedder.get_embedding(query)
        if not emb or not self.entries:
            return []
        q = np.array(emb)
        qn = np.linalg.norm(q)
        scored = []
        for e in self.entries:
            v = e["embedding"]
            sim = np.dot(q, v) / (np.linalg.norm(v) * qn)
            scored.append((sim, e["text"]))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [t for _, t in scored[:top_k]]
