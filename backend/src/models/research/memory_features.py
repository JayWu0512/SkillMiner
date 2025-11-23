"""Local, self-contained memory utilities for research LSTM experiments.

This mirrors the structure of `stm.py` and `ltm.py` but intentionally avoids:
- Supabase
- backend `src.*` imports
- external OpenAI / Supabase clients

Everything here is pure Python + optional `transformers` / `spacy`, and it can
be run directly via `python` from this folder.
"""

from typing import List, Dict, Any
import math
import re

import numpy as np

try:
    import spacy
except ImportError:  # pragma: no cover - optional dependency
    spacy = None

try:
    from transformers import pipeline, AutoTokenizer
except ImportError:  # pragma: no cover - optional dependency
    pipeline = None  # type: ignore
    AutoTokenizer = None  # type: ignore


# ===== Basic STM-style helpers (local copy, no backend config) =====


class TokenLimitController:
    """
    Token limit controller.

    - If `transformers` + AutoTokenizer are available, use the tokenizer of the
      same summarization model as `SummarizationLayer` (distilbart-cnn) to count
      real tokens and truncate by token ids.
    - Otherwise fall back to a simple char→token heuristic (~4 chars/token).
    """

    def __init__(self, max_tokens: int = 256, model_name: str | None = None):
        self.max_tokens = max_tokens
        self.model_name = model_name or "sshleifer/distilbart-cnn-12-6"
        self.tokenizer = None  # lazy init

    # ---------- internal helpers ----------

    def _ensure_tokenizer(self) -> None:
        """Lazy load tokenizer. If anything fails, keep tokenizer=None."""
        if self.tokenizer is not None:
            return
        if AutoTokenizer is None:
            return
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception:
            self.tokenizer = None

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.

        - Use real tokenizer token count if available.
        - Else use ~4 chars per token heuristic.
        """
        if not text:
            return 0

        self._ensure_tokenizer()
        if self.tokenizer is not None:
            try:
                ids = self.tokenizer.encode(text, add_special_tokens=False)
                return len(ids)
            except Exception:
                pass

        # Fallback heuristic
        return len(text) // 4

    # ---------- public API ----------

    def truncate(self, text: str, max_tokens: int | None = None) -> str:
        if not text:
            return ""
        if max_tokens is None:
            max_tokens = self.max_tokens

        self._ensure_tokenizer()
        if self.tokenizer is not None:
            try:
                ids = self.tokenizer.encode(text, add_special_tokens=False)
                if len(ids) <= max_tokens:
                    return text

                truncated_ids = ids[:max_tokens]
                truncated_text = self.tokenizer.decode(
                    truncated_ids,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True,
                )
                return truncated_text.strip() + "..."
            except Exception:
                pass

        # Fallback：char-based heuristic (~4 chars/token)
        estimated = len(text) // 4
        if estimated <= max_tokens:
            return text

        max_chars = max_tokens * 4
        truncated = text[:max_chars]

        # Prefer cutting on a sentence boundary if reasonably close
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")
        cutoff = max(last_period, last_newline)
        if cutoff > max_chars * 0.8:
            return truncated[: cutoff + 1]

        return truncated + "..."


class SummarizationLayer:
    """
    Very small summarization wrapper.

    - If `transformers` is available, use a local summarization pipeline.
    - Otherwise fall back to a simple extractive summarizer (first N sentences).
    """

    def __init__(self, model_name: str | None = None):
        # Use a much smaller model for faster training:
        # - distilbart-cnn-12-6 is ~60% smaller than bart-large
        # - Set to None to disable HF summarization entirely (uses extractive fallback)
        self.model_name = model_name or "sshleifer/distilbart-cnn-12-6"
        self._summarizer = None
        self._init_model()

    def _init_model(self) -> None:
        if pipeline is None:
            return
        try:
            self._summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=-1,  # keep on CPU for stability
            )
        except Exception:
            # If model download fails, keep fallback behaviour
            self._summarizer = None

    def _extractive_summarize(self, text: str, max_sentences: int = 5) -> str:
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return text
        return ". ".join(sentences[:max_sentences]) + "."

    def summarize(self, text: str, max_tokens: int = 256) -> str:
        if not text or not text.strip():
            return ""

        # Fallback: simple extractive summary
        if self._summarizer is None:
            return self._extractive_summarize(text)

        # Keep input size reasonable
        words = text.split()
        if len(words) > 1024:
            text = " ".join(words[:1024])

        # Choose a smaller max_length to keep inference fast and avoid HF warnings
        # about max_length >> input_length. Aim for ~80% of input length but also
        # cap by max_tokens and enforce a reasonable floor.
        input_len = len(text.split())
        if input_len <= 0:
            return text

        # At most half of the token budget and at most 80% of input length
        rough_cap = min(max_tokens // 2, int(input_len * 0.8))
        max_len = max(32, rough_cap)
        min_len = max(8, max_len // 4)

        try:
            result = self._summarizer(
                text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,
            )
            if isinstance(result, list) and result:
                return result[0].get("summary_text", text)
            return text
        except Exception:
            return self._extractive_summarize(text)


# ===== NER / semantic helpers (local + in-memory only) =====


class NERExtractor:
    """
    Lightweight NER extractor.

    - If spaCy + English model is available, use it.
    - Otherwise fall back to simple keyword-based extraction.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self.nlp = None
        self._init_model()

    def _init_model(self) -> None:
        if spacy is None:
            return
        try:
            self.nlp = spacy.load(self.model_name)
        except Exception:
            # If model not present, leave `nlp` as None and use fallback
            self.nlp = None

    def _fallback(self, text: str) -> Dict[str, List[str]]:
        text_lower = text.lower()
        entities: Dict[str, List[str]] = {
            "skills": [],
            "companies": [],
            "roles": [],
            "locations": [],
            "other": [],
        }

        tech_keywords = [
            "python",
            "java",
            "javascript",
            "typescript",
            "react",
            "sql",
            "aws",
            "docker",
            "kubernetes",
        ]
        for kw in tech_keywords:
            if kw in text_lower:
                entities["skills"].append(kw.title())
        return entities

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        if not text or not text.strip():
            return {
                "skills": [],
                "companies": [],
                "roles": [],
                "locations": [],
                "other": [],
            }

        if self.nlp is None:
            return self._fallback(text)

        doc = self.nlp(text)
        entities: Dict[str, List[str]] = {
            "skills": [],
            "companies": [],
            "roles": [],
            "locations": [],
            "other": [],
        }

        for ent in doc.ents:
            if ent.label_ in ("ORG",):
                entities["companies"].append(ent.text)
            elif ent.label_ in ("GPE", "LOC"):
                entities["locations"].append(ent.text)
            else:
                entities["other"].append(ent.text)

        # De-duplicate
        for k in entities:
            entities[k] = sorted(set(entities[k]))
        return entities


class SemanticEmbedder:
    """
    Very small **local** semantic embedder.

    To keep research experiments self-contained and offline, this does NOT call
    OpenAI or Supabase. Instead it maps text deterministically to a fixed-size
    pseudo-random vector using a hash seed.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def get_embedding(self, text: str) -> List[float] | None:
        if not text or not text.strip():
            return None
        # Deterministic seed from text
        seed = abs(hash(text)) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.normal(size=self.dim).astype(np.float32)
        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec.tolist()
        return (vec / norm).tolist()


# ===== Thin feature wrappers used by the research models =====


class SummarizationFeature:
    def __init__(self, max_tokens: int = 256, model_name: str | None = None):
        self.summarizer = SummarizationLayer(model_name=model_name)
        self.token_controller = TokenLimitController(
            max_tokens=max_tokens,
            model_name=model_name or "sshleifer/distilbart-cnn-12-6",
        )

    def summarize(self, text: str) -> str:
        raw = self.summarizer.summarize(
            text, max_tokens=self.token_controller.max_tokens
        )
        return self.token_controller.truncate(raw)


class TokenLimitFeature:
    def __init__(self, max_tokens: int, model_name: str | None = None):
        self.controller = TokenLimitController(
            max_tokens=max_tokens,
            model_name=model_name or "sshleifer/distilbart-cnn-12-6",
        )

    def truncate(self, text: str) -> str:
        return self.controller.truncate(text)


class NERFeature:
    def __init__(self):
        self.ner = NERExtractor()

    def extract(self, text: str) -> Dict[str, List[str]]:
        return self.ner.extract_entities(text)


class LocalSemanticMemory:
    """Simplified LTM: stored only in RAM with local, deterministic embeddings."""

    def __init__(self):
        self.embedder = SemanticEmbedder()
        self.entries: List[Dict[str, Any]] = []

    def add(self, text: str) -> None:
        emb = self.embedder.get_embedding(text)
        if not emb:
            return
        self.entries.append(
            {"text": text, "embedding": np.asarray(emb, dtype=np.float32)}
        )

    def search(self, query: str, top_k: int = 5) -> List[str]:
        emb = self.embedder.get_embedding(query)
        if not emb or not self.entries:
            return []

        q = np.asarray(emb, dtype=np.float32)
        qn = np.linalg.norm(q)
        if qn == 0:
            return []

        scored: List[tuple[float, str]] = []
        for e in self.entries:
            v = e["embedding"]
            vn = np.linalg.norm(v)
            if vn == 0:
                continue
            sim = float(np.dot(q, v) / (qn * vn))
            scored.append((sim, e["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]
