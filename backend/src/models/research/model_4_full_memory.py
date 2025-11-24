# models/research/model_4_full_memory.py
from typing import List

from base_lstm_model import BaseMemoryLSTM
from memory_features import (
    SummarizationFeature,
    TokenLimitFeature,
    NERFeature,
    LocalSemanticMemory,
)

# Local default to keep this module self‑contained for research
STM_MAX_TOKENS = 256


class FullMemoryLSTM(BaseMemoryLSTM):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int, domain: str = "general"):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        self.sum_feat = SummarizationFeature()
        self.tok_feat = TokenLimitFeature(STM_MAX_TOKENS)
        self.ner_feat = NERFeature(domain=domain)
        self.semantic_mem = LocalSemanticMemory()

    def ingest_history(self, history: List[str]):
        """Before training, load all historical paragraphs into semantic memory."""
        for h in history:
            self.semantic_mem.add(h)

    def build_memory_context(self, history: List[str], current: str) -> str:
        # 1. STM-style summary (same as model 3)
        if not history:
            return ""
        history_text = "\n".join(history)
        summary = self.sum_feat.summarize(history_text)
        summary = self.tok_feat.truncate(summary)

        # 2. NER on summary (same as model 3)
        entities = self.ner_feat.extract(summary)
        entity_str_parts = []
        # Support general, finance, python, and pets domains
        if entities.get("skills"):
            entity_str_parts.append("Skills: " + ", ".join(entities["skills"]))
        if entities.get("products"):  # Finance domain
            entity_str_parts.append("Products: " + ", ".join(entities["products"]))
        if entities.get("roles"):
            entity_str_parts.append("Roles: " + ", ".join(entities["roles"]))
        if entities.get("financial_terms"):  # Finance domain
            entity_str_parts.append("Financial Terms: " + ", ".join(entities["financial_terms"]))
        if entities.get("companies"):
            entity_str_parts.append("Companies: " + ", ".join(entities["companies"]))
        if entities.get("libraries"):  # Python domain
            entity_str_parts.append("Libraries: " + ", ".join(entities["libraries"]))
        if entities.get("concepts"):  # Python domain
            entity_str_parts.append("Concepts: " + ", ".join(entities["concepts"]))
        if entities.get("tools"):  # Python domain
            entity_str_parts.append("Tools: " + ", ".join(entities["tools"]))
        if entities.get("breeds"):  # Pets domain
            entity_str_parts.append("Breeds: " + ", ".join(entities["breeds"]))
        if entities.get("health_issues"):  # Pets domain
            entity_str_parts.append("Health Issues: " + ", ".join(entities["health_issues"]))
        if entities.get("care_topics"):  # Pets domain
            entity_str_parts.append("Care Topics: " + ", ".join(entities["care_topics"]))

        entity_block = "\n".join(entity_str_parts)
        
        # 3. Semantic search for long-term relevant paragraphs
        # Use smaller top_k and filter by similarity threshold to avoid noise
        # Note: Hash-based embeddings may not be truly semantic, so use conservative threshold
        retrieved = self.semantic_mem.search(current, top_k=2, min_similarity=0.0)
        
        # Filter out retrieved memories that are already in recent history
        # to avoid redundancy
        retrieved_filtered = []
        for r in retrieved:
            # Skip if this retrieval is already in the recent history window
            is_duplicate = any(r.strip() in h.strip() or h.strip() in r.strip() 
                             for h in history[-5:])  # Check last 5 history items
            if not is_duplicate:
                retrieved_filtered.append(r)
        
        # Build result: start with summary + entities (like model 3)
        result = summary
        if entity_block:
            result += "\n\n" + entity_block
        
        # Add semantic memories only if they add value
        if retrieved_filtered:
            # Truncate each retrieved item if too long to avoid overwhelming input
            retrieved_parts = []
            for r in retrieved_filtered[:2]:  # Max 2 items
                if len(r) > 150:
                    r = r[:147] + "..."
                retrieved_parts.append(r)
            retrieved_block = "\n\n".join(retrieved_parts)
            result += "\n\n" + retrieved_block

        return result
