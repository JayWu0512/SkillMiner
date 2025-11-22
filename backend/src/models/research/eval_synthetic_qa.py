"""
Evaluate models on SkillMiner synthetic QA.

Recommended CSV location:
    models/research/data/skillminer_qa_synthetic.csv

CSV format:
    qa_id,question,answer
"""

import csv
import os
import difflib
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional, Dict

# ==== Import BaseMemoryLSTM (from base_lstm_model.py) ====
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
except ImportError:  # pragma: no cover
    SummarizationOnlyLSTM = None  # type: ignore
    SumTokenLimitLSTM = None  # type: ignore
    SumTokNerLSTM = None  # type: ignore
    FullMemoryLSTM = None  # type: ignore


# ============== Basic utilities ==============


def normalize_text(text: str) -> str:
    """Simple normalize: lower + strip + collapse multiple whitespace."""
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


def load_qa_csv(path: str) -> List[Tuple[int, str, str]]:
    """Read CSV and return [(qa_id, question, answer), ...]"""
    rows: List[Tuple[int, str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            qa_id = int(r["qa_id"])
            q = r["question"]
            a = r["answer"]
            rows.append((qa_id, q, a))
    return rows


def text_similarity(a: str, b: str) -> float:
    """Compute a 0–1 similarity using difflib."""
    return difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


# ============== Evaluation interface ==============


@dataclass
class QAModelWrapper:
    name: str
    predict_fn: Callable[[List[str], str], str]


def evaluate_model(
    model: QAModelWrapper,
    data: List[Tuple[int, str, str]],
    history_size: int = 20,
    sim_threshold: float = 0.8,
) -> float:

    total = 0
    correct = 0

    history_texts: List[str] = []  # ["Q: ...\nA: ...", ...]

    for qa_id, q, true_a in data:
        history = history_texts[-history_size:]

        pred_a = model.predict_fn(history, q)

        sim = text_similarity(pred_a, true_a)
        if sim >= sim_threshold:
            correct += 1
        total += 1

        history_texts.append(f"Q: {q}\nA: {true_a}")

    acc = correct / total if total else 0.0
    print(
        f"[{model.name}] accuracy = {acc:.3f} "
        f"(sim >= {sim_threshold}, {correct}/{total})"
    )
    return acc


# ============== Base LSTM slots (four research variants) ==============

_base_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore  # SummarizationOnly
_sumtok_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore
_sumtokner_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore
_fullmem_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore
_device: Optional[torch.device] = None

# ---- Simple character-level tokenizer/decoder (same as logs eval) ----
_PAD_CHAR = "<pad>"
_ALL_CHARS = [chr(i) for i in range(32, 127)]  # printable ASCII
_ITOS: List[str] = [_PAD_CHAR] + _ALL_CHARS
_STOI: Dict[str, int] = {ch: idx for idx, ch in enumerate(_ITOS)}
_VOCAB_SIZE = len(_ITOS)
_MAX_SEQ_LEN = 256


def encode_text(text: str) -> torch.Tensor:
    """Encode free text into a (1, seq_len) tensor of token ids."""
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
    """Initialize the four QA LSTM variants (untrained for now)."""
    global _base_lstm_instance, _sumtok_lstm_instance, _sumtokner_lstm_instance, _fullmem_lstm_instance, _device

    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    vocab_size = _VOCAB_SIZE
    emb_dim = 128
    hidden_dim = 128

    if BaseMemoryLSTM is None:
        return

    # 1) Summarization-only
    if _base_lstm_instance is None and SummarizationOnlyLSTM is not None:
        m = SummarizationOnlyLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        m.to(_device)
        m.eval()
        _base_lstm_instance = m  # type: ignore

    # 2) Summarization + token limit
    if _sumtok_lstm_instance is None and SumTokenLimitLSTM is not None:
        m = SumTokenLimitLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        m.to(_device)
        m.eval()
        _sumtok_lstm_instance = m  # type: ignore

    # 3) Summarization + token limit + NER
    if _sumtokner_lstm_instance is None and SumTokNerLSTM is not None:
        m = SumTokNerLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        m.to(_device)
        m.eval()
        _sumtokner_lstm_instance = m  # type: ignore

    # 4) Full memory
    if _fullmem_lstm_instance is None and FullMemoryLSTM is not None:
        m = FullMemoryLSTM(vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim)
        m.to(_device)
        m.eval()
        _fullmem_lstm_instance = m  # type: ignore


def _qa_predict_with_model(
    model: "BaseMemoryLSTM",  # type: ignore[name-defined]
    history: List[str],
    question: str,
) -> str:
    """Shared helper: run a QA LSTM model and decode a tiny answer token."""
    assert _device is not None

    input_text = model.prepare_input_text(history, question)
    token_ids = encode_text(input_text).to(_device)
    with torch.no_grad():
        logits = model(token_ids)  # type: ignore[call-arg]

    last_logits = logits[0, -1]
    pred_id = int(torch.argmax(last_logits).item())
    pred_char = decode_ids([pred_id]).strip()

    if pred_char:
        return f"SkillMiner answers: {pred_char}"
    return "SkillMiner analyzes your input and prepares a response."


def model0_base_lstm_predict(history: List[str], question: str) -> str:
    """
    BaseLSTM baseline:
    - Use BaseMemoryLSTM.prepare_input_text(history, question)
    - Convert text -> tokens -> LSTM -> decode

    Currently returns effectively random text until the model is trained,
    but it does exercise the full LSTM forward/decoding path.
    """
    init_base_lstm()

    if _base_lstm_instance is None or _device is None:
        # Fallback stub if something failed
        return "SkillMiner analyzes your input and prepares a response."

    return _qa_predict_with_model(_base_lstm_instance, history, question)  # type: ignore[arg-type]


def model1_sumtok_predict(history: List[str], question: str) -> str:
    """SumTokenLimitLSTM: summarization + token limit memory."""
    init_base_lstm()
    if _sumtok_lstm_instance is None or _device is None:
        return "SkillMiner analyzes your input and prepares a response."
    return _qa_predict_with_model(_sumtok_lstm_instance, history, question)  # type: ignore[arg-type]


def model2_sumtokner_predict(history: List[str], question: str) -> str:
    """SumTokNerLSTM: summarization + token limit + NER memory."""
    init_base_lstm()
    if _sumtokner_lstm_instance is None or _device is None:
        return "SkillMiner analyzes your input and prepares a response."
    return _qa_predict_with_model(_sumtokner_lstm_instance, history, question)  # type: ignore[arg-type]


def model3_fullmem_predict(history: List[str], question: str) -> str:
    """FullMemoryLSTM: STM + NER + local semantic memory."""
    init_base_lstm()
    if _fullmem_lstm_instance is None or _device is None:
        return "SkillMiner analyzes your input and prepares a response."
    return _qa_predict_with_model(_fullmem_lstm_instance, history, question)  # type: ignore[arg-type]


# ============== main ==============


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "data", "skillminer_qa_synthetic.csv")

    print(f"Loading dataset from: {csv_path}")
    data = load_qa_csv(csv_path)

    models = [
        QAModelWrapper("LSTM_1_SummarizationOnly", model0_base_lstm_predict),
        QAModelWrapper("LSTM_2_SumTokenLimit", model1_sumtok_predict),
        QAModelWrapper("LSTM_3_SumTokNER", model2_sumtokner_predict),
        QAModelWrapper("LSTM_4_FullMemory", model3_fullmem_predict),
    ]

    for m in models:
        evaluate_model(m, data, history_size=20, sim_threshold=0.6)


if __name__ == "__main__":
    main()
