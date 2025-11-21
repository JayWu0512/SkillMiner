# models/research/model_4_full_memory.py
from typing import List
from .base_lstm_model import BaseMemoryLSTM
from .memory_features import (
    SummarizationFeature,
    TokenLimitFeature,
    NERFeature,
    LocalSemanticMemory,
)
from src.core.config import STM_MAX_TOKENS


class FullMemoryLSTM(BaseMemoryLSTM):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        self.sum_feat = SummarizationFeature()
        self.tok_feat = TokenLimitFeature(STM_MAX_TOKENS)
        self.ner_feat = NERFeature()
        self.semantic_mem = LocalSemanticMemory()

    def ingest_history(self, history: List[str]):
        """Before training, load all historical paragraphs into semantic memory."""
        for h in history:
            self.semantic_mem.add(h)

    def build_memory_context(self, history: List[str], current: str) -> str:
        # 1. STM-style summary
        history_text = "\n".join(history)
        summary = self.sum_feat.summarize(history_text) if history else ""
        summary = self.tok_feat.truncate(summary) if summary else ""

        # 2. NER on summary
        ner_block = ""
        if summary:
            entities = self.ner_feat.extract(summary)
            parts = []
            if entities.get("skills"):
                parts.append("Skills: " + ", ".join(entities["skills"]))
            if entities.get("roles"):
                parts.append("Roles: " + ", ".join(entities["roles"]))
            if entities.get("companies"):
                parts.append("Companies: " + ", ".join(entities["companies"]))
            if parts:
                ner_block = "\n".join(parts)

        # 3. semantic search for long-term relevant paragraphs
        retrieved = self.semantic_mem.search(current, top_k=3)
        retrieved_block = "\n\n".join(retrieved) if retrieved else ""

        blocks = []
        if summary:
            blocks.append("=== STM Summary ===\n" + summary)
        if ner_block:
            blocks.append("=== Entities ===\n" + ner_block)
        if retrieved_block:
            blocks.append("=== Semantic Memories ===\n" + retrieved_block)

        return "\n\n".join(blocks)
