# models/research/base_lstm_model.py
from abc import ABC, abstractmethod
from typing import List
import torch
import torch.nn as nn


class BaseMemoryLSTM(ABC, nn.Module):
    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    @abstractmethod
    def build_memory_context(self, history: List[str], current: str) -> str:
        """Subclasses determine how to combine memory."""
        ...

    def forward(self, token_ids: torch.Tensor):
        # token_ids: (batch, seq_len)
        emb = self.embedding(token_ids)
        out, _ = self.lstm(emb)
        logits = self.fc(out)
        return logits

    def prepare_input_text(self, history: List[str], current: str) -> str:
        """Research focus: align history + memory as LSTM input text."""
        mem_ctx = self.build_memory_context(history, current)
        if mem_ctx:
            return mem_ctx + "\n\n" + current
        return current
