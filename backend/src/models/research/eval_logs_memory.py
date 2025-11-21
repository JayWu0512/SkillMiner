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


# ============== Base LSTM slot (KEY) ==============

_base_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore


def init_base_lstm() -> None:
    """
    Initialize the Base LSTM model instance.

    Later, you can replace this with:
        from my_log_lstm import LogBaseLSTM
        global _base_lstm_instance
        _base_lstm_instance = LogBaseLSTM(vocab_size=..., emb_dim=..., hidden_dim=...)
        _base_lstm_instance.load_state_dict(torch.load("..."))

    Currently a stub to allow eval file to run without blocker.
    """
    global _base_lstm_instance
    if _base_lstm_instance is not None:
        return

    if BaseMemoryLSTM is None:
        # Not implemented/import failed yet, skip
        return

    # TODO: Replace with your Log-based BaseMemoryLSTM subclass here
    return


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

    if _base_lstm_instance is None:
        # Temporary stub: replace once you train the real LogBaseLSTM
        return "The current level is 1."

    # When actually integrated with LSTM, it would look like this:
    # input_text = _base_lstm_instance.prepare_input_text(history, question)
    # ids = tokenizer.encode(input_text)
    # logits = _base_lstm_instance(torch.tensor([ids]))
    # pred_ids = decode_greedy(logits)
    # return tokenizer.decode(pred_ids)

    # For now, return same stub to avoid crashes before tokenizer integration
    return "The current level is 1."


# ============== Four stub models (baseline heuristic) ==============


def model1_predict(history: List[str], question: str) -> str:
    """
    Model 1 stub: ignores history completely, returns fixed level.
    Baseline: predicts level = 1
    """
    return "The current level is 1."


def model2_predict(history: List[str], question: str) -> str:
    """
    Model 2 stub: estimates level based on history length.
    Shows a more "dynamic" baseline approach.
    """
    # Heuristic: level increases by 1 per 5 logs
    approx_level = max(1, len(history) // 5)
    return f"The current level is {approx_level}."


def model3_predict(history: List[str], question: str) -> str:
    """
    Model 3 stub: searches history for last mention of 'level' or 'gained X exp',
    then uses simple heuristic to infer level.
    Currently weak baseline since synthetic messages don't directly mention level.
    """
    # Find last record related to exp (currently just for demonstration)
    for msg in reversed(history):
        if "gained" in msg or "completed a lesson" in msg:
            break
    # Placeholder guess
    return "The current level is 2."


def model4_predict(history: List[str], question: str) -> str:
    """
    Model 4 stub: simulates 'FullMemory' version.
    Demonstrates: uses history length for more sophisticated heuristic.
    """
    # Slightly more aggressive than model2
    approx_level = max(1, len(history) // 4)
    return f"The current level is {approx_level}."


# ============== main ==============


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "data", "skillminer_logs_synthetic.csv")

    print(f"Loading logs from: {csv_path}")
    logs = load_logs_csv(csv_path)

    models = [
        LogModelWrapper("BaseLSTM_NoMemory", model0_base_lstm_predict),
        LogModelWrapper("LogModel_1_BaselineConstant", model1_predict),
        LogModelWrapper("LogModel_2_BaselineHistoryLen", model2_predict),
        LogModelWrapper("LogModel_3_ExpHeuristic", model3_predict),
        LogModelWrapper("LogModel_4_FullMemoryHeuristic", model4_predict),
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
