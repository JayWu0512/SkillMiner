"""
Evaluate task-oriented memory: can the model correctly infer
"what task should I perform for this user?" from SkillMiner-style requests.

CSV Location (recommended):
    models/research/data/task_oriented_skillminer_synthetic.csv

CSV Fields:
    task_id,user_id,request,task_label,task_summary
"""

import csv
import os
import difflib
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional, Dict

# ===== Import BaseMemoryLSTM here =====
try:
    from base_lstm_model import BaseMemoryLSTM
except ImportError:
    BaseMemoryLSTM = None  # type: ignore

import torch

try:
    from model_1_summarization import SummarizationOnlyLSTM
    from model_2_sum_toklimit import SumTokenLimitLSTM
    from model_3_sum_tok_ner import SumTokNerLSTM
    from model_4_full_memory import FullMemoryLSTM
except ImportError:  # pragma: no cover
    SummarizationOnlyLSTM = None  # type: ignore
    SumTokenLimitLSTM = None  # type: ignore
    SumTokNerLSTM = None  # type: ignore
    FullMemoryLSTM = None  # type: ignore


# ============== Basic utilities ==============


def normalize_text(text: str) -> str:
    """Simple normalize: lowercase + strip whitespace + merge multiple spaces."""
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


def text_similarity(a: str, b: str) -> float:
    """Calculate 0–1 similarity score using difflib."""
    return difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def load_task_csv(path: str) -> List[Tuple[int, str, str, str, str]]:
    """
    Load CSV and return list of:
        (task_id, user_id, request, task_label, task_summary)
    """
    rows: List[Tuple[int, str, str, str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            tid = int(r["task_id"])
            user_id = r["user_id"]
            request = r["request"]
            label = r["task_label"]
            summary = r["task_summary"]
            rows.append((tid, user_id, request, label, summary))
    return rows


# ============== Evaluation interface ==============


@dataclass
class TaskModelWrapper:
    name: str
    predict_fn: Callable[[List[str], str], str]


def evaluate_task_model(
    model: TaskModelWrapper,
    data: List[Tuple[int, str, str, str, str]],
    history_size: int = 20,
    sim_threshold: float = 0.7,
) -> float:
    """
    For each request:
        history = previous user requests (treated as conversation history)
        question = "Based on this request, what task should you perform for user X?"

    Then check if model's answer similarity to task_summary >= threshold.
    """
    total = 0
    correct = 0

    # history_messages: store "user_id: request => task_summary" as context
    history_messages: List[str] = []

    for task_id, user_id, request, label, summary in data:
        history = history_messages[-history_size:]

        question = (
            f"User {user_id} just said: '{request}'. "
            f"What task should you perform for this user?"
        )

        pred = model.predict_fn(history, question)
        sim = text_similarity(pred, summary)

        if sim >= sim_threshold:
            correct += 1
        total += 1

        history_messages.append(f"user {user_id}: {request} => {summary}")

    acc = correct / total if total else 0.0
    print(
        f"[{model.name}] task accuracy = {acc:.3f} "
        f"(sim >= {sim_threshold}, {correct}/{total})"
    )
    return acc


# ============== Base LSTM slots (key part) ==============

_base_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore  # SummarizationOnly
_sumtok_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore
_sumtokner_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore
_fullmem_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore
_device: Optional[torch.device] = None

# Reuse the same simple char-level tokenizer as other evals
_PAD_CHAR = "<pad>"
_ALL_CHARS = [chr(i) for i in range(32, 127)]
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
    return torch.tensor([ids], dtype=torch.long)


def decode_ids(ids: List[int]) -> str:
    chars: List[str] = []
    for idx in ids:
        if 0 <= idx < len(_ITOS):
            ch = _ITOS[idx]
            if ch != _PAD_CHAR:
                chars.append(ch)
    return "".join(chars)


def init_base_lstm() -> None:
    """
    Initialize your Base LSTM model here.

    Currently uses the research LSTM variants as concrete implementations,
    untrained, just to exercise the full path.
    """
    global _base_lstm_instance, _sumtok_lstm_instance, _sumtokner_lstm_instance, _fullmem_lstm_instance, _device
    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if BaseMemoryLSTM is None:
        return

    vocab_size = _VOCAB_SIZE
    emb_dim = 128
    hidden_dim = 128

    # 1) Summarization-only
    if _base_lstm_instance is None and SummarizationOnlyLSTM is not None:
        m = SummarizationOnlyLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
        m.to(_device)
        m.eval()
        _base_lstm_instance = m  # type: ignore

    # 2) SumTokenLimit
    if _sumtok_lstm_instance is None and SumTokenLimitLSTM is not None:
        m = SumTokenLimitLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
        m.to(_device)
        m.eval()
        _sumtok_lstm_instance = m  # type: ignore

    # 3) SumTokNER
    if _sumtokner_lstm_instance is None and SumTokNerLSTM is not None:
        m = SumTokNerLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
        m.to(_device)
        m.eval()
        _sumtokner_lstm_instance = m  # type: ignore

    # 4) FullMemory
    if _fullmem_lstm_instance is None and FullMemoryLSTM is not None:
        m = FullMemoryLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
        m.to(_device)
        m.eval()
        _fullmem_lstm_instance = m  # type: ignore


def _task_predict_with_model(
    model: "BaseMemoryLSTM",  # type: ignore[name-defined]
    history: List[str],
    question: str,
) -> str:
    assert _device is not None

    input_text = model.prepare_input_text(history, question)
    token_ids = encode_text(input_text).to(_device)
    with torch.no_grad():
        logits = model(token_ids)  # type: ignore[call-arg]

    last_logits = logits[0, -1]
    pred_id = int(torch.argmax(last_logits).item())
    pred_char = decode_ids([pred_id]).strip()

    if pred_char:
        return f"{pred_char} the user's study plan"

    return "adjust the user's study plan"


def model0_base_lstm_predict(history: List[str], question: str) -> str:
    """
    Base LSTM (no memory augmentation) evaluation interface.

    Key point: use BaseMemoryLSTM.prepare_input_text(history, question)
               to align history into a single input string, then decode with LSTM.

    Currently uses SummarizationOnlyLSTM.
    """
    init_base_lstm()

    if _base_lstm_instance is None or _device is None:
        # No actual model yet → use baseline stub
        return "adjust the user's study plan"

    return _task_predict_with_model(_base_lstm_instance, history, question)  # type: ignore[arg-type]


def model1_sumtok_predict(history: List[str], question: str) -> str:
    """SumTokenLimitLSTM."""
    init_base_lstm()
    if _sumtok_lstm_instance is None or _device is None:
        return "adjust the user's study plan"
    return _task_predict_with_model(_sumtok_lstm_instance, history, question)  # type: ignore[arg-type]


def model2_sumtokner_predict(history: List[str], question: str) -> str:
    """SumTokNerLSTM."""
    init_base_lstm()
    if _sumtokner_lstm_instance is None or _device is None:
        return "adjust the user's study plan"
    return _task_predict_with_model(_sumtokner_lstm_instance, history, question)  # type: ignore[arg-type]


def model3_fullmem_predict(history: List[str], question: str) -> str:
    """FullMemoryLSTM."""
    init_base_lstm()
    if _fullmem_lstm_instance is None or _device is None:
        return "adjust the user's study plan"
    return _task_predict_with_model(_fullmem_lstm_instance, history, question)  # type: ignore[arg-type]


# ============== main ==============


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(
        current_dir, "data", "task_oriented_skillminer_synthetic.csv"
    )

    print(f"Loading task dataset from: {csv_path}")
    data = load_task_csv(csv_path)

    models = [
        TaskModelWrapper("LSTM_1_SummarizationOnly", model0_base_lstm_predict),
        TaskModelWrapper("LSTM_2_SumTokenLimit", model1_sumtok_predict),
        TaskModelWrapper("LSTM_3_SumTokNER", model2_sumtokner_predict),
        TaskModelWrapper("LSTM_4_FullMemory", model3_fullmem_predict),
    ]

    for m in models:
        evaluate_task_model(m, data, history_size=20, sim_threshold=0.7)


if __name__ == "__main__":
    main()
