# models/research/model_3_sum_tok_ner.py
from typing import List

from base_lstm_model import BaseMemoryLSTM
from memory_features import SummarizationFeature, TokenLimitFeature, NERFeature

# Local default to keep this module self‑contained for research
STM_MAX_TOKENS = 256


class SumTokNerLSTM(BaseMemoryLSTM):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        self.sum_feat = SummarizationFeature()
        self.tok_feat = TokenLimitFeature(STM_MAX_TOKENS)
        self.ner_feat = NERFeature()

    def build_memory_context(self, history: List[str], current: str) -> str:
        if not history:
            return ""
        history_text = "\n".join(history)
        summary = self.sum_feat.summarize(history_text)
        summary = self.tok_feat.truncate(summary)

        entities = self.ner_feat.extract(summary)
        entity_str_parts = []
        if entities.get("skills"):
            entity_str_parts.append("Skills: " + ", ".join(entities["skills"]))
        if entities.get("roles"):
            entity_str_parts.append("Roles: " + ", ".join(entities["roles"]))
        if entities.get("companies"):
            entity_str_parts.append("Companies: " + ", ".join(entities["companies"]))

        entity_block = "\n".join(entity_str_parts)
        return summary + ("\n\n" + entity_block if entity_block else "")
