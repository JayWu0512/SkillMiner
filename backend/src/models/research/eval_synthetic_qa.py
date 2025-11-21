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
from typing import List, Tuple, Callable, Optional

# ==== Import BaseMemoryLSTM (from base_lstm_model.py) ====
try:
    from base_lstm_model import BaseMemoryLSTM
except ImportError:
    BaseMemoryLSTM = None  # type: ignore


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


# ============== Base LSTM slot (new) ==============

_base_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore


def init_base_lstm():
    """Initialize the base LSTM model. Load the real model here later."""
    global _base_lstm_instance
    if _base_lstm_instance is not None:
        return

    if BaseMemoryLSTM is None:
        return

    # TODO — replace with your trained QA LSTM in the future
    # from qa_lstm import QABaseLSTM
    # _base_lstm_instance = QABaseLSTM(...)
    return


def model0_base_lstm_predict(history: List[str], question: str) -> str:
    """
    BaseLSTM baseline:
    - Use BaseMemoryLSTM.prepare_input_text(history, question)
    - Convert text -> tokens -> LSTM -> decode

    Currently returns a stub until tokenizer & trained model are plugged in.
    """
    init_base_lstm()

    if _base_lstm_instance is None:
        return "SkillMiner analyzes your input and prepares a response."

    # The real implementation would look like this:
    # input_text = _base_lstm_instance.prepare_input_text(history, question)
    # ids = tokenizer.encode(input_text)
    # logits = _base_lstm_instance(torch.tensor([ids]))
    # pred_ids = decode_greedy(logits)
    # return tokenizer.decode(pred_ids)

    return "SkillMiner analyzes your input and prepares a response."


# ============== Other 4 stub models ==============


def model1_predict(history: List[str], question: str) -> str:
    return "SkillMiner analyzes your target role and builds a personalized roadmap."


def model2_predict(history: List[str], question: str) -> str:
    return f"In SkillMiner, the system reads your question '{question}' and creates a simple plan."


def model3_predict(history: List[str], question: str) -> str:
    for ctx in reversed(history):
        lines = ctx.splitlines()
        if len(lines) >= 2 and lines[0].startswith("Q:"):
            past_q = lines[0][2:].strip()
            past_a = lines[1][2:].strip()
            if normalize_text(past_q) == normalize_text(question):
                return past_a
    return "SkillMiner uses your resume and target role to prioritize missing skills."


def model4_predict(history: List[str], question: str) -> str:
    for ctx in reversed(history):
        lines = ctx.splitlines()
        if len(lines) >= 2 and lines[0].startswith("Q:"):
            past_q = lines[0][2:].strip()
            past_a = lines[1][2:].strip()
            if text_similarity(past_q, question) >= 0.9:
                return past_a
    return "SkillMiner combines skill gaps, weekly hours, and target role to generate a detailed study plan."


# ============== main ==============


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "data", "skillminer_qa_synthetic.csv")

    print(f"Loading dataset from: {csv_path}")
    data = load_qa_csv(csv_path)

    models = [
        QAModelWrapper(
            "BaseLSTM_NoMemory", model0_base_lstm_predict
        ),  # newly added model
        QAModelWrapper("Model_1_SummarizationOnly", model1_predict),
        QAModelWrapper("Model_2_SumTokenLimit", model2_predict),
        QAModelWrapper("Model_3_SumTokNER", model3_predict),
        QAModelWrapper("Model_4_FullMemory", model4_predict),
    ]

    for m in models:
        evaluate_model(m, data, history_size=20, sim_threshold=0.6)


if __name__ == "__main__":
    main()
