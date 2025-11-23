# models/research/model_0_base.py
from typing import List

from base_lstm_model import BaseMemoryLSTM


class BaseLSTM(BaseMemoryLSTM):
    """
    Baseline LSTM model with no memory components.
    
    This model only uses the current question without any history or memory features.
    It serves as a baseline to compare against models with memory capabilities.
    Expected to perform worse than all other models.
    """

    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int):
        super().__init__(vocab_size, emb_dim, hidden_dim)
        # No memory features - just the base LSTM

    def build_memory_context(self, history: List[str], current: str) -> str:
        """
        Return empty string - no memory context.
        
        This means prepare_input_text will only use the current question,
        ignoring all history. This makes it the simplest possible baseline.
        """
        return ""

