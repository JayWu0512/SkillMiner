# models/research/model_3_sum_tok_ner.py
from typing import List

from base_lstm_model import BaseMemoryLSTM
from memory_features import SummarizationFeature, TokenLimitFeature, NERFeature

# Local default to keep this module self‑contained for research
STM_MAX_TOKENS = 256


class SumTokNerLSTM(BaseMemoryLSTM):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int, domain: str = "general"):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        self.sum_feat = SummarizationFeature()
        self.tok_feat = TokenLimitFeature(STM_MAX_TOKENS)
        self.ner_feat = NERFeature(domain=domain)

    def build_memory_context(self, history: List[str], current: str) -> str:
        if not history:
            return ""
        history_text = "\n".join(history)
        summary = self.sum_feat.summarize(history_text)
        summary = self.tok_feat.truncate(summary)

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
        return summary + ("\n\n" + entity_block if entity_block else "")
