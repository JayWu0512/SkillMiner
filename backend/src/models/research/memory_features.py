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

    def __init__(self, model_name: str | None = None, use_gpu: bool | None = None):
        # Use a much smaller model for faster training:
        # - distilbart-cnn-12-6 is ~60% smaller than bart-large
        # - Set to None to disable HF summarization entirely (uses extractive fallback)
        self.model_name = model_name or "sshleifer/distilbart-cnn-12-6"
        self._summarizer = None
        # Auto-detect GPU if use_gpu is None, otherwise use provided value
        if use_gpu is None:
            try:
                import torch
                self.use_gpu = torch.cuda.is_available()
            except ImportError:
                self.use_gpu = False
        else:
            self.use_gpu = use_gpu
        self._init_model()

    def _init_model(self) -> None:
        if pipeline is None:
            return
        try:
            # Use GPU if available and requested, otherwise CPU
            device = 0 if self.use_gpu else -1
            device_name = "GPU" if self.use_gpu else "CPU"
            self._summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=device,
                batch_size=8 if self.use_gpu else 1,  # Batch processing on GPU for efficiency
            )
            print(f"HuggingFace summarization pipeline initialized on {device_name}")
        except Exception as e:
            # If GPU fails, try falling back to CPU
            if self.use_gpu:
                try:
                    print(f"GPU initialization failed ({e}), falling back to CPU...")
                    self._summarizer = pipeline(
                        "summarization",
                        model=self.model_name,
                        device=-1,
                    )
                    print("HuggingFace summarization pipeline initialized on CPU (fallback)")
                except Exception:
                    self._summarizer = None
            else:
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

        # Keep input size reasonable - truncate based on actual tokens to avoid HF warnings
        # The model has a max input length of 1024 tokens, so we'll truncate at ~1000 to be safe
        try:
            # Try to use the tokenizer if available to do proper token-based truncation
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            tokens = tokenizer.encode(text, add_special_tokens=False, max_length=1000, truncation=True)
            text = tokenizer.decode(tokens, skip_special_tokens=True)
        except Exception:
            # Fallback to word-based truncation (less precise but works)
            words = text.split()
            if len(words) > 800:  # ~800 words ≈ 1000 tokens (conservative estimate)
                text = " ".join(words[:800])

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
            # Pipeline automatically batches when batch_size > 1, but for single calls
            # we still call it normally - the batching happens internally when processing
            # multiple items through the pipeline
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
    
    def summarize_batch(self, texts: List[str], max_tokens: int = 256) -> List[str]:
        """
        Summarize a batch of texts more efficiently on GPU.
        This is useful when processing multiple texts at once.
        """
        if not texts:
            return []
        
        # Fallback: simple extractive summary
        if self._summarizer is None:
            return [self._extractive_summarize(text) for text in texts]
        
        # Process texts in batches
        results = []
        for text in texts:
            if not text or not text.strip():
                results.append("")
                continue
            
            # Truncate input (same logic as single summarize)
            try:
                from transformers import AutoTokenizer
                tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                tokens = tokenizer.encode(text, add_special_tokens=False, max_length=1000, truncation=True)
                text = tokenizer.decode(tokens, skip_special_tokens=True)
            except Exception:
                words = text.split()
                if len(words) > 800:
                    text = " ".join(words[:800])
            
            input_len = len(text.split())
            if input_len <= 0:
                results.append(text)
                continue
            
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
                    results.append(result[0].get("summary_text", text))
                else:
                    results.append(text)
            except Exception:
                results.append(self._extractive_summarize(text))
        
        return results


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

        # Domain-specific keywords
        finance_keywords = {
            "skills": [  # Products/Technologies
                "gpu", "cpu", "dpu", "soc", "rtx", "cuda", "tensor", "dlss",
                "h100", "a100", "geforce", "quadro", "tesla", "dgx", "bluefield",
                "infiniBand", "ethernet", "fpga", "asic", "ai", "ml", "deep learning"
            ],
            "roles": [  # Financial terms
                "fiscal year", "revenue", "acquisition", "merger", "ipo", "dividend",
                "earnings", "profit", "loss", "margin", "ebitda", "cash flow",
                "balance sheet", "income statement", "10-k", "10-q", "sec filing"
            ]
        }
        
        python_keywords = {
            "skills": [  # Python libraries/packages
                "pandas", "numpy", "sklearn", "scikit-learn", "keras", "tensorflow",
                "pytorch", "fuzzywuzzy", "zipfile", "pickle", "datetime", "threading",
                "flask", "django", "pytest", "conftest", "spacy", "nltk", "openai"
            ],
            "roles": [  # Programming concepts/topics
                "gradient clipping", "lstm", "rnn", "neural network", "machine learning",
                "operator overloading", "threading", "multithreading", "generator",
                "yield", "decorator", "context manager", "class", "inheritance",
                "polymorphism", "encapsulation", "exception handling", "async", "await",
                "cross validation", "smote", "auc", "f1 score", "precision", "recall",
                "tokenizer", "embedding", "vectorizer", "tfidf", "countvectorizer"
            ],
            "companies": [  # Tools/platforms
                "pycharm", "jupyter", "anaconda", "pip", "conda", "aws", "ec2",
                "google app engine", "bash", "shell", "linux", "windows"
            ]
        }
        
        pets_keywords = {
            "skills": [  # Dog and cat breeds
                "labrador", "retriever", "golden retriever", "german shepherd", "bulldog",
                "beagle", "poodle", "rottweiler", "yorkshire terrier", "dachshund",
                "siberian husky", "great dane", "boxer", "doberman", "australian shepherd",
                "corgi", "shih tzu", "boston terrier", "pomeranian", "chihuahua",
                "maltese", "basset hound", "mastiff", "saint bernard", "border collie",
                "persian", "maine coon", "british shorthair", "ragdoll", "american shorthair",
                "scottish fold", "sphynx", "russian blue", "siamese", "abyssinian",
                "bengal", "birman", "himalayan", "norwegian forest", "oriental shorthair",
                "korat", "javanese", "japanese bobtail", "havana brown", "burmilla",
                "burmese", "bombay", "akita", "collie", "setter", "spaniel", "terrier"
            ],
            "roles": [  # Health issues and medical conditions
                "diabetes", "arthritis", "cancer", "heart disease", "kidney disease",
                "liver disease", "urinary tract", "infection", "parasite", "flea",
                "tick", "heartworm", "allergy", "asthma", "obesity", "anemia",
                "cataract", "glaucoma", "deafness", "blindness", "dental", "tooth",
                "gum", "vomiting", "diarrhea", "constipation", "fever", "lethargy",
                "seizure", "hyperthyroidism", "hypothyroidism", "pancreatitis",
                "gastric", "volvulus", "colitis", "megacolon", "lymphoma", "leukemia"
            ],
            "companies": [  # Care topics: training, grooming, feeding, behavior
                "training", "grooming", "feeding", "nutrition", "exercise", "walking",
                "vaccination", "spaying", "neutering", "litter box", "scratching",
                "bathing", "brushing", "nail trimming", "dental care", "socialization",
                "behavior", "aggression", "anxiety", "stress", "play", "toys",
                "carrier", "crate", "leash", "harness", "food", "treats", "diet",
                "weight", "obesity", "hydration", "water", "shelter", "bedding"
            ]
        }

        text_lower = text.lower()
        
        # Extract finance keywords (if finance domain)
        for keyword in finance_keywords["skills"]:
            if keyword in text_lower:
                entities["skills"].append(keyword.title())
        for keyword in finance_keywords["roles"]:
            if keyword in text_lower:
                entities["roles"].append(keyword.title())
        
        # Extract Python keywords (if python domain)
        for keyword in python_keywords["skills"]:
            if keyword in text_lower:
                entities["skills"].append(keyword.title())
        for keyword in python_keywords["roles"]:
            if keyword in text_lower:
                entities["roles"].append(keyword.title())
        for keyword in python_keywords["companies"]:
            if keyword in text_lower:
                entities["companies"].append(keyword.title())
        
        # Extract pets keywords (if pets domain)
        for keyword in pets_keywords["skills"]:
            if keyword in text_lower:
                entities["skills"].append(keyword.title())
        for keyword in pets_keywords["roles"]:
            if keyword in text_lower:
                entities["roles"].append(keyword.title())
        for keyword in pets_keywords["companies"]:
            if keyword in text_lower:
                entities["companies"].append(keyword.title())

        for ent in doc.ents:
            if ent.label_ in ("ORG",):
                entities["companies"].append(ent.text)
            elif ent.label_ in ("GPE", "LOC"):
                entities["locations"].append(ent.text)
            elif ent.label_ in ("MONEY", "PERCENT", "DATE"):
                # Financial entities
                if any(term in text_lower for term in ["fiscal", "quarter", "year", "$", "billion", "million"]):
                    entities["roles"].append(ent.text)
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
    def __init__(self, domain: str = "general"):
        """
        Initialize NER feature extractor.
        
        Args:
            domain: "general" for skills/roles/companies (default),
                   "finance" for products/financial_terms/companies,
                   "python" for libraries/concepts/tools,
                   "pets" for breeds/health_issues/care_topics
        """
        self.ner = NERExtractor()
        self.domain = domain

    def extract(self, text: str) -> Dict[str, List[str]]:
        entities = self.ner.extract_entities(text)
        
        # Map entities based on domain
        if self.domain == "finance":
            # For finance: map to products, financial_terms, companies
            mapped = {
                "products": entities.get("skills", []),  # Technologies/products
                "financial_terms": entities.get("roles", []),  # Financial concepts
                "companies": entities.get("companies", []),
            }
            return mapped
        elif self.domain == "python":
            # For python: map to libraries, concepts, tools
            mapped = {
                "libraries": entities.get("skills", []),  # Python libraries/packages
                "concepts": entities.get("roles", []),  # Programming concepts/topics
                "tools": entities.get("companies", []),  # Development tools/platforms
            }
            return mapped
        elif self.domain == "pets":
            # For pets: map to breeds, health_issues, care_topics
            mapped = {
                "breeds": entities.get("skills", []),  # Dog and cat breeds
                "health_issues": entities.get("roles", []),  # Health problems and medical conditions
                "care_topics": entities.get("companies", []),  # Training, grooming, feeding, behavior
            }
            return mapped
        else:
            # For general: keep skills, roles, companies
            return {
                "skills": entities.get("skills", []),
                "roles": entities.get("roles", []),
                "companies": entities.get("companies", []),
            }


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

    def search(self, query: str, top_k: int = 5, min_similarity: float = -1.0) -> List[str]:
        """
        Search for similar entries.
        
        Args:
            query: Query text
            top_k: Maximum number of results to return
            min_similarity: Minimum similarity score to include (default: -1.0, no filtering)
        """
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
            if sim >= min_similarity:
                scored.append((sim, e["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]
