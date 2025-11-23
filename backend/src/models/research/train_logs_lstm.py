"""
Train LSTM-based log-memory models on the synthetic SkillMiner logs dataset.

This script trains ONE of the four research variants at a time:
  - summarization_only
  - sum_token_limit
  - sum_tok_ner
  - full_memory

The training objective is simple:
  - For each log event, build the same (history, question) input used in eval_logs_memory.py:
        history = previous log messages (up to history_size)
        question = "After this event, what is the current level of user X?"
  - Use the chosen LSTM to build a memory-augmented input string.
  - Run it through the shared char-level tokenizer + LSTM.
  - Train the model to predict the final LEVEL DIGIT as a single character
    from the last time step logits (0–9).

You can run for example:

    cd backend/src/models/research
    python train_logs_lstm.py --model_type summarization_only --epochs 3
"""

import argparse
import os
import csv
from typing import List, Dict, Optional, Tuple

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from base_lstm_model import BaseMemoryLSTM
from model_1_summarization import SummarizationOnlyLSTM
from model_2_sum_toklimit import SumTokenLimitLSTM
from model_3_sum_tok_ner import SumTokNerLSTM
from model_4_full_memory import FullMemoryLSTM


# ==== Char-level tokenizer (must match eval_logs_memory.py) ====

_PAD_CHAR = "<pad>"
_ALL_CHARS = [chr(i) for i in range(32, 127)]  # printable ASCII
_ITOS: List[str] = [_PAD_CHAR] + _ALL_CHARS
_STOI: Dict[str, int] = {ch: idx for idx, ch in enumerate(_ITOS)}
_VOCAB_SIZE = len(_ITOS)
_MAX_SEQ_LEN = 256


def encode_text(text: str) -> torch.Tensor:
    text = text or ""
    text = text[:_MAX_SEQ_LEN]
    ids: List[int] = []
    for ch in text:
        ids.append(_STOI.get(ch, _STOI[" "]))
    if not ids:
        ids = [_STOI[" "]]
    return torch.tensor(ids, dtype=torch.long)  # (seq_len,)


# ==== Dataset over log events ====


class LogsLevelDataset(Dataset):
    """
    Sequence-style dataset over the logs CSV.

    Each item i (corresponding to row i) returns:
      - history_messages: list[str] of previous messages (at most history_size)
      - question: "After this event, what is the current level of user X?"
      - target_digit: int in [0..9] (the final digit of level)
      
    If cache_path is provided and exists, will load pre-computed input texts from disk.
    """

    def __init__(self, rows: List[Dict[str, str]], history_size: int = 50, cache_path: Optional[str] = None, model: Optional[BaseMemoryLSTM] = None):
        self.rows = rows
        self.history_size = history_size
        self.cache_path = cache_path
        self.model = model
        
        # Precompute history for each index
        self._histories: List[List[str]] = []
        history: List[str] = []
        for r in rows:
            self._histories.append(history[-history_size :].copy())
            history.append(r["message"])
        
        # Optionally pre-compute and cache input texts (with summaries) for massive speedup
        self._cached_input_texts: Optional[List[str]] = None
        if cache_path and os.path.exists(cache_path):
            print(f"Loading cached input texts from {cache_path}...")
            with open(cache_path, 'r', encoding='utf-8') as f:
                import json
                self._cached_input_texts = json.load(f)
            print(f"Loaded {len(self._cached_input_texts)} cached inputs.")
        elif model is not None:
            # Pre-compute all summaries once
            print("Pre-computing summaries (this happens once and is cached for future runs)...")
            self._cached_input_texts = []
            for i in range(len(self.rows)):
                if i % 50 == 0:
                    print(f"  Pre-computing {i}/{len(self.rows)}...")
                row = self.rows[i]
                user_id = row["user_id"]
                question = f"After this event, what is the current level of user {user_id}?"
                input_text = model.prepare_input_text(self._histories[i], question)  # type: ignore[arg-type]
                self._cached_input_texts.append(input_text)
            
            # Save cache
            if cache_path:
                os.makedirs(os.path.dirname(cache_path) if os.path.dirname(cache_path) else '.', exist_ok=True)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(self._cached_input_texts, f)
                print(f"Saved cached input texts to {cache_path}")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> Tuple[List[str], str, int, Optional[str]]:
        row = self.rows[idx]
        user_id = row["user_id"]
        level_true = int(row["level"])
        history = self._histories[idx]

        question = f"After this event, what is the current level of user {user_id}?"
        
        # If we have cached input text, return it; otherwise return None and compute in training loop
        cached_text = self._cached_input_texts[idx] if self._cached_input_texts else None

        # We'll train to predict the last digit of the level (0–9)
        digit = int(str(level_true)[-1])
        return history, question, digit, cached_text


def load_logs_csv(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    rows.sort(key=lambda r: int(r["log_id"]))
    return rows


# ==== Model factory ====


def build_model(model_type: str, device: torch.device) -> BaseMemoryLSTM:
    vocab_size = _VOCAB_SIZE
    emb_dim = 128
    hidden_dim = 128

    if model_type == "summarization_only":
        m = SummarizationOnlyLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
    elif model_type == "sum_token_limit":
        m = SumTokenLimitLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
    elif model_type == "sum_tok_ner":
        m = SumTokNerLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
    elif model_type == "full_memory":
        m = FullMemoryLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    m.to(device)
    return m


# ==== Training loop ====


def train_one_epoch(
    model: BaseMemoryLSTM,
    dataloader: DataLoader,
    device: torch.device,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
) -> float:
    model.train()
    total_loss = 0.0
    total_batches = 0

    for batch in dataloader:
        # With collate_fn=lambda x: list(zip(*x)), each batch is:
        #   history:     List[List[str]]
        #   question:    List[str]
        #   digit:       List[int]
        #   cached_text: List[Optional[str]]
        history, question, digit, cached_text = batch

        batch_size = len(history)

        # Use cached input texts if available (much faster!), otherwise compute on-the-fly
        input_texts: List[str] = []
        for i, (h, q, cached) in enumerate(zip(history, question, cached_text)):
            if cached is not None:
                input_texts.append(cached)  # Use pre-computed summary
            else:
                input_texts.append(model.prepare_input_text(list(h), q))  # type: ignore[arg-type]

        # Encode and pad into a batch
        encoded = [encode_text(t) for t in input_texts]  # list[(seq_len,)]
        seq_lens = [e.size(0) for e in encoded]
        max_len = max(seq_lens)

        batch_ids = torch.full(
            (batch_size, max_len), _STOI[" "], dtype=torch.long
        )  # pad with space
        for i, e in enumerate(encoded):
            batch_ids[i, : e.size(0)] = e

        batch_ids = batch_ids.to(device)  # (batch, seq_len)
        targets = torch.tensor(digit, dtype=torch.long, device=device)  # (batch,)

        optimizer.zero_grad()
        logits = model(batch_ids)  # (batch, seq_len, vocab)

        # Use the last time step for each sequence
        last_logits = logits[torch.arange(batch_size), [l - 1 for l in seq_lens], :]  # (batch, vocab)

        # Map digit (0–9) to corresponding char index in vocab
        digit_chars = [str(int(d.item())) for d in targets]
        target_ids = torch.tensor(
            [_STOI.get(ch, _STOI["0"]) for ch in digit_chars], dtype=torch.long, device=device
        )

        loss = criterion(last_logits, target_ids)
        loss.backward()
        optimizer.step()

        total_loss += float(loss.item())
        total_batches += 1

    return total_loss / max(total_batches, 1)


@torch.no_grad()
def evaluate_level_accuracy(
    model: BaseMemoryLSTM,
    dataloader: DataLoader,
    device: torch.device,
) -> float:
    """Rudimentary eval: exact digit prediction accuracy."""
    model.eval()
    correct = 0
    total = 0
    digit_pred_count = 0  # Track how many predictions are digits
    last_pred_chars = []  # Store last batch predictions for debugging
    last_target_chars = []  # Store last batch targets for debugging

    for batch in dataloader:
        history, question, digit, cached_text = batch
        batch_size = len(history)
        # Use cached input texts if available
        input_texts: List[str] = []
        for h, q, cached in zip(history, question, cached_text):
            if cached is not None:
                input_texts.append(cached)  # Use pre-computed summary
            else:
                input_texts.append(model.prepare_input_text(list(h), q))  # type: ignore[arg-type]

        encoded = [encode_text(t) for t in input_texts]
        seq_lens = [e.size(0) for e in encoded]
        max_len = max(seq_lens)

        batch_ids = torch.full(
            (batch_size, max_len), _STOI[" "], dtype=torch.long
        )
        for i, e in enumerate(encoded):
            batch_ids[i, : e.size(0)] = e

        batch_ids = batch_ids.to(device)
        logits = model(batch_ids)  # (batch, seq_len, vocab)

        last_logits = logits[torch.arange(batch_size), [l - 1 for l in seq_lens], :]
        pred_ids = torch.argmax(last_logits, dim=-1)  # (batch,)

        # Map digit targets to vocab indices
        targets = torch.tensor(digit, dtype=torch.long, device=device)
        digit_chars = [str(int(d.item())) for d in targets]
        target_ids = torch.tensor(
            [_STOI.get(ch, _STOI["0"]) for ch in digit_chars], dtype=torch.long, device=device
        )
        
        # Debug: Check what characters the model is predicting
        pred_chars = [_ITOS[int(pid.item())] if 0 <= pid.item() < len(_ITOS) else "?" for pid in pred_ids]
        # Count how many predictions are actually digits vs other chars
        digit_count = sum(1 for pc in pred_chars if pc.isdigit())
        
        # Store last batch for debugging
        last_pred_chars = pred_chars.copy()
        last_target_chars = digit_chars.copy()
        
        if total == 0:  # Print debug info for first batch
            print(f"  [Debug] Sample predictions (first batch): pred_chars={pred_chars[:5]}, target_chars={digit_chars[:5]}")
        
        correct += int((pred_ids == target_ids).sum().item())
        total += batch_size
        digit_pred_count += digit_count  # Track how many predictions are digits

    acc = correct / max(total, 1)
    
    # Always print debug info if accuracy is concerning
    if acc <= 0.15:
        print(f"  [Warning] Low val accuracy ({acc:.3f}). Model may be predicting non-digit chars or needs more training.")
        print(f"  [Debug] {digit_pred_count}/{total} predictions were digits (vs targets which are all digits)")
        if last_pred_chars:  # Print sample predictions from last batch
            print(f"  [Debug] Sample pred chars (last batch): {last_pred_chars[:10]}, target chars: {last_target_chars[:10]}")
            # Count character frequencies in last batch
            from collections import Counter
            char_counts = Counter(last_pred_chars[:50])
            print(f"  [Debug] Most common pred chars (last batch): {dict(char_counts.most_common(10))}")
    return acc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_type",
        type=str,
        default="summarization_only",
        choices=["summarization_only", "sum_token_limit", "sum_tok_ner", "full_memory"],
        help="Which LSTM variant to train.",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16, help="Increase to 64 for faster training. Reduce if OOM.")
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--history_size", type=int, default=50, help="Reduce to 30 for faster training. Increase for better context.")
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints_logs")
    parser.add_argument("--disable_summarization", action="store_true", help="Disable HF summarization entirely (uses simple extractive fallback) for much faster training. Useful for quick experiments.")
    parser.add_argument("--cache_dir", type=str, default="cache_logs", help="Directory to store pre-computed summaries. Speeds up training dramatically after first run.")
    args = parser.parse_args()
    
    # If --disable_summarization, set model_name to None to skip HF summarization
    if args.disable_summarization:
        import memory_features
        # Patch the SummarizationLayer to use None (extractive fallback)
        original_init = memory_features.SummarizationLayer.__init__
        def patched_init(self, model_name=None):
            original_init(self, model_name=None)  # Force None = no HF model
        memory_features.SummarizationLayer.__init__ = patched_init

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "data", "skillminer_logs_synthetic.csv")
    print(f"Loading logs from: {csv_path}")
    rows = load_logs_csv(csv_path)

    # Build model first (needed for pre-computing summaries)
    model = build_model(args.model_type, device)
    
    # Create cache directory
    os.makedirs(args.cache_dir, exist_ok=True)
    cache_path = os.path.join(args.cache_dir, f"{args.model_type}_inputs.json")
    
    # Create dataset with optional caching
    dataset = LogsLevelDataset(rows, history_size=args.history_size, cache_path=cache_path, model=model)
    
    # Simple split: 80% train, 20% val (use fixed seed for reproducibility)
    split = int(0.8 * len(dataset))
    generator = torch.Generator().manual_seed(42)  # Fixed seed for reproducible splits
    train_ds, val_ds = torch.utils.data.random_split(dataset, [split, len(dataset) - split], generator=generator)
    
    # Rebuild model after dataset (in case we want fresh instance)
    model = build_model(args.model_type, device)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=lambda x: list(zip(*x)))
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, collate_fn=lambda x: list(zip(*x)))

    model = build_model(args.model_type, device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    print(f"Training model_type={args.model_type} on device={device} ...")
    if args.disable_summarization:
        print("  [Note] Summarization disabled - using fast extractive fallback")
    print(f"  [Note] Expected training time: ~10-30 min for 3 epochs (varies by GPU)")
    print(f"  [Note] Target val_digit_acc: >0.5 (ideally >0.8).")
    best_val_acc = 0.0

    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, device, optimizer, criterion)
        val_acc = evaluate_level_accuracy(model, val_loader, device)

        print(f"[Epoch {epoch}] train_loss={train_loss:.4f}  val_digit_acc={val_acc:.3f}")

        # Save best checkpoint
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            ckpt_path = os.path.join(
                args.checkpoint_dir, f"{args.model_type}_best.pt"
            )
            torch.save(model.state_dict(), ckpt_path)
            print(f"  Saved checkpoint to {ckpt_path}")


if __name__ == "__main__":
    main()


