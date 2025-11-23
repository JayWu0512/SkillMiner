"""
Evaluate log-based memory: can the model infer the current level of each user
from a sequence of SkillMiner logs?

CSV Location (Recommended):
    models/research/data/skillminer_logs_synthetic.csv

CSV Format:
    log_id,timestamp,user_id,event_type,exp_delta,total_exp,level,message
"""

import csv
import os
import re
from dataclasses import dataclass
from typing import List, Tuple, Callable, Dict, Optional

# ==== Import BaseMemoryLSTM (aligned with base_lstm_model.py) ====
try:
    from base_lstm_model import BaseMemoryLSTM
except ImportError:
    BaseMemoryLSTM = None  # type: ignore

import torch

try:
    # Use the research LSTM variants as concrete BaseMemoryLSTM implementations
    from model_1_summarization import SummarizationOnlyLSTM
    from model_2_sum_toklimit import SumTokenLimitLSTM
    from model_3_sum_tok_ner import SumTokNerLSTM
    from model_4_full_memory import FullMemoryLSTM
except ImportError:
    SummarizationOnlyLSTM = None  # type: ignore
    SumTokenLimitLSTM = None  # type: ignore
    SumTokNerLSTM = None  # type: ignore
    FullMemoryLSTM = None  # type: ignore


# ============== utils ==============

LEVEL_INT_REGEX = re.compile(r"(-?\d+)")


def extract_first_int(text: str) -> int | None:
    """Extract the first integer from text to use as predicted level."""
    if not text:
        return None
    m = LEVEL_INT_REGEX.search(text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def load_logs_csv(path: str) -> List[Dict[str, str]]:
    """Load logs CSV and return list of dict rows."""
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    # Sort by log_id to ensure chronological order
    rows.sort(key=lambda r: int(r["log_id"]))
    return rows


# ============== Evaluation Interface ==============


@dataclass
class LogModelWrapper:
    name: str
    predict_fn: Callable[[List[str], str], str]


def evaluate_level_prediction(
    model: LogModelWrapper,
    logs: List[Dict[str, str]],
    history_size: int = 50,
    allow_off_by_one: bool = False,
) -> float:
    """
    Test: after each log, ask:
        "After this event, what is the current level of user X?"
    Check if the model's predicted number matches the true level.

    :param model: LogModelWrapper
    :param logs: logs data
    :param history_size: maximum number of historical logs to show to the model
    :param allow_off_by_one: if True, prediction within ±1 of true value counts as correct
    """
    total = 0
    correct = 0

    # history: contains only message text
    history_messages: List[str] = []

    for row in logs:
        user_id = row["user_id"]
        level_true = int(row["level"])
        msg = row["message"]

        # Prepare history (excluding current row)
        history = history_messages[-history_size:]

        # Question: focused on the user
        question = f"After this event, what is the current level of user {user_id}?"

        # Model prediction
        pred_text = model.predict_fn(history, question)

        # Extract number from answer
        pred_level = extract_first_int(pred_text)

        if pred_level is not None:
            if not allow_off_by_one:
                if pred_level == level_true:
                    correct += 1
            else:
                if abs(pred_level - level_true) <= 1:
                    correct += 1

        total += 1

        # Add current log message to history
        history_messages.append(msg)

    acc = correct / total if total else 0.0
    mode_str = "exact" if not allow_off_by_one else "off-by-one"
    print(
        f"[{model.name}] level prediction accuracy ({mode_str}) = "
        f"{acc:.3f} ({correct}/{total})"
    )
    return acc


# ============== Base LSTM slots (KEY) ==============

_base_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore  # SummarizationOnly
_sumtok_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore  # SumTokenLimit
_sumtokner_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore  # SumTokNER
_fullmem_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore  # FullMemory
_device: Optional[torch.device] = None

# ---- Simple character-level tokenizer/decoder (self-contained) ----
_PAD_CHAR = "<pad>"
_ALL_CHARS = [chr(i) for i in range(32, 127)]  # printable ASCII
_ITOS: List[str] = [_PAD_CHAR] + _ALL_CHARS
_STOI: Dict[str, int] = {ch: idx for idx, ch in enumerate(_ITOS)}
_VOCAB_SIZE = len(_ITOS)
_MAX_SEQ_LEN = 256

# Where training script saves checkpoints (see train_logs_lstm.py)
CHECKPOINT_DIR = "checkpoints_logs"


def encode_text(text: str) -> torch.Tensor:
    """
    Convert arbitrary text into a 1D tensor of token ids (length <= _MAX_SEQ_LEN).
    This is deliberately simple and deterministic so we can plug in the LSTM
    before we have a real tokenizer or training.
    """
    text = text or ""
    text = text[:_MAX_SEQ_LEN]  # Truncate to avoid very long sequences
    ids: List[int] = []
    for ch in text:
        ids.append(_STOI.get(ch, _STOI[" "]))  # unknown chars → space
    if not ids:
        ids = [_STOI[" "]]
    return torch.tensor([ids], dtype=torch.long)  # (batch=1, seq_len)


def decode_ids(ids: List[int]) -> str:
    """Turn a list of token ids back into a text string."""
    chars: List[str] = []
    for idx in ids:
        if 0 <= idx < len(_ITOS):
            ch = _ITOS[idx]
            if ch != _PAD_CHAR:
                chars.append(ch)
    return "".join(chars)


def init_base_lstm() -> None:
    """
    Initialize all four research LSTM variants (untrained).
    """
    global _base_lstm_instance, _sumtok_lstm_instance, _sumtokner_lstm_instance, _fullmem_lstm_instance, _device

    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    vocab_size = _VOCAB_SIZE
    emb_dim = 128
    hidden_dim = 128

    # 1) Summarization-only
    if _base_lstm_instance is None and SummarizationOnlyLSTM is not None and BaseMemoryLSTM is not None:
        m = SummarizationOnlyLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        ckpt_path = os.path.join(CHECKPOINT_DIR, "summarization_only_best.pt")
        if os.path.exists(ckpt_path):
            m.load_state_dict(torch.load(ckpt_path, map_location=_device))
            print(f"[eval_logs] Loaded checkpoint: {ckpt_path}")
        m.to(_device)
        m.eval()
        _base_lstm_instance = m  # type: ignore

    # 2) Summarization + token limit
    if _sumtok_lstm_instance is None and SumTokenLimitLSTM is not None and BaseMemoryLSTM is not None:
        m = SumTokenLimitLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        ckpt_path = os.path.join(CHECKPOINT_DIR, "sum_token_limit_best.pt")
        if os.path.exists(ckpt_path):
            m.load_state_dict(torch.load(ckpt_path, map_location=_device))
            print(f"[eval_logs] Loaded checkpoint: {ckpt_path}")
        m.to(_device)
        m.eval()
        _sumtok_lstm_instance = m  # type: ignore

    # 3) Summarization + token limit + NER
    if _sumtokner_lstm_instance is None and SumTokNerLSTM is not None and BaseMemoryLSTM is not None:
        m = SumTokNerLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        ckpt_path = os.path.join(CHECKPOINT_DIR, "sum_tok_ner_best.pt")
        if os.path.exists(ckpt_path):
            m.load_state_dict(torch.load(ckpt_path, map_location=_device))
            print(f"[eval_logs] Loaded checkpoint: {ckpt_path}")
        m.to(_device)
        m.eval()
        _sumtokner_lstm_instance = m  # type: ignore

    # 4) Full memory (STM + NER + local semantic memory)
    if _fullmem_lstm_instance is None and FullMemoryLSTM is not None and BaseMemoryLSTM is not None:
        m = FullMemoryLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        ckpt_path = os.path.join(CHECKPOINT_DIR, "full_memory_best.pt")
        if os.path.exists(ckpt_path):
            m.load_state_dict(torch.load(ckpt_path, map_location=_device))
            print(f"[eval_logs] Loaded checkpoint: {ckpt_path}")
        m.to(_device)
        m.eval()
        _fullmem_lstm_instance = m  # type: ignore


def _predict_with_lstm(
    model: "BaseMemoryLSTM",  # type: ignore[name-defined]
    history: List[str],
    question: str,
) -> str:
    """
    Shared helper: run a given BaseMemoryLSTM and decode a level string.
    """
    assert _device is not None

    # 1) Let the model construct its memory-augmented input text
    input_text = model.prepare_input_text(history, question)

    # 2) Encode text → token ids
    token_ids = encode_text(input_text).to(_device)  # (1, seq_len)

    # 3) Run through LSTM
    with torch.no_grad():
        logits = model(token_ids)  # type: ignore[call-arg]
        # logits: (batch=1, seq_len, vocab)

    # 4) Greedy decode characters from the last time step
    last_step_logits = logits[0, -1]  # (vocab,)
    pred_id = int(torch.argmax(last_step_logits).item())
    pred_text = decode_ids([pred_id]).strip()

    if pred_text and pred_text[0].isdigit():
        return f"The current level is {pred_text[0]}."

    # Fallback if decoding didn't yield a digit
    return "The current level is 1."


def model0_base_lstm_predict(history: List[str], question: str) -> str:
    """
    Base LSTM (without additional memory augmentation) prediction interface.

    Concept:
      - Use BaseMemoryLSTM.build_memory_context(history, question)
        + prepare_input_text(history, question)
        to combine logs history into a long input text, feed to LSTM to generate answer.

    Currently: stub to avoid blocking other experiments.
               Replace this once you train the real LogBaseLSTM.
    """
    init_base_lstm()

    if _base_lstm_instance is None or _device is None:
        # If something went wrong with initialization, fall back to old stub
        return "The current level is 1."

    return _predict_with_lstm(_base_lstm_instance, history, question)  # type: ignore[arg-type]


def model1_sumtok_predict(history: List[str], question: str) -> str:
    """SumTokenLimitLSTM: summarization + token-limit memory."""
    init_base_lstm()
    if _sumtok_lstm_instance is None or _device is None:
        return "The current level is 1."
    return _predict_with_lstm(_sumtok_lstm_instance, history, question)  # type: ignore[arg-type]


def model2_sumtokner_predict(history: List[str], question: str) -> str:
    """SumTokNerLSTM: summarization + token-limit + NER memory."""
    init_base_lstm()
    if _sumtokner_lstm_instance is None or _device is None:
        return "The current level is 1."
    return _predict_with_lstm(_sumtokner_lstm_instance, history, question)  # type: ignore[arg-type]


def model3_fullmem_predict(history: List[str], question: str) -> str:
    """FullMemoryLSTM: STM + NER + local semantic memory."""
    init_base_lstm()
    if _fullmem_lstm_instance is None or _device is None:
        return "The current level is 1."
    return _predict_with_lstm(_fullmem_lstm_instance, history, question)  # type: ignore[arg-type]


# ============== main ==============


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "data", "skillminer_logs_synthetic.csv")

    print(f"Loading logs from: {csv_path}")
    logs = load_logs_csv(csv_path)

    models = [
        LogModelWrapper("LSTM_1_SummarizationOnly", model0_base_lstm_predict),
        LogModelWrapper("LSTM_2_SumTokenLimit", model1_sumtok_predict),
        LogModelWrapper("LSTM_3_SumTokNER", model2_sumtokner_predict),
        LogModelWrapper("LSTM_4_FullMemory", model3_fullmem_predict),
    ]

    print("=== Exact match accuracy (no off-by-one) ===")
    for m in models:
        evaluate_level_prediction(
            m,
            logs,
            history_size=50,
            allow_off_by_one=False,
        )

    print("\n=== Off-by-one accuracy (|pred - true| <= 1) ===")
    for m in models:
        evaluate_level_prediction(
            m,
            logs,
            history_size=50,
            allow_off_by_one=True,
        )


if __name__ == "__main__":
    main()
