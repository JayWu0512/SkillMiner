# models/research/model_2_sum_toklimit.py
from typing import List

from base_lstm_model import BaseMemoryLSTM
from memory_features import SummarizationFeature, TokenLimitFeature

# Local default to keep this module self‑contained for research
STM_MAX_TOKENS = 256


class SumTokenLimitLSTM(BaseMemoryLSTM):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        self.sum_feat = SummarizationFeature()
        self.tok_feat = TokenLimitFeature(max_tokens=STM_MAX_TOKENS)

    def build_memory_context(self, history: List[str], current: str) -> str:
        if not history:
            return ""
        history_text = "\n".join(history)
        summary = self.sum_feat.summarize(history_text)
        return self.tok_feat.truncate(summary)
