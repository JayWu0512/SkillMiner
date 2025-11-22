# models/research/model_1_summarization.py
from typing import List

# Import as local modules so this file can be run directly from the research folder
from base_lstm_model import BaseMemoryLSTM
from memory_features import SummarizationFeature


class SummarizationOnlyLSTM(BaseMemoryLSTM):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        self.sum_feat = SummarizationFeature()

    def build_memory_context(self, history: List[str], current: str) -> str:
        if not history:
            return ""
        # Summarize history as a single text
        history_text = "\n".join(history)
        return self.sum_feat.summarize(history_text)
