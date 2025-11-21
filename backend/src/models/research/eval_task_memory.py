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
from typing import List, Tuple, Callable, Optional

# ===== Import BaseMemoryLSTM here =====
try:
    from base_lstm_model import BaseMemoryLSTM
except ImportError:
    BaseMemoryLSTM = None  # type: ignore


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


# ============== Base LSTM slot (key part) ==============

_base_lstm_instance: Optional["BaseMemoryLSTM"] = None  # type: ignore


def init_base_lstm() -> None:
    """
    Initialize your Base LSTM model here (you can modify this later):

    Example:
        from my_tokenizer import tokenizer
        from my_model_impl import MyBaseTaskLSTM

        global _base_lstm_instance
        _base_lstm_instance = MyBaseTaskLSTM(...)
        _base_lstm_instance.load_state_dict(torch.load("..."))

    Currently left empty to allow the code to run; wire it up when ready.
    """
    global _base_lstm_instance
    if _base_lstm_instance is not None:
        return

    if BaseMemoryLSTM is None:
        # Import failed, skip (will use fallback)
        return

    # TODO: Replace with your actual subclass & weight loading
    # Example:
    # from my_task_lstm import TaskBaseLSTM
    # _base_lstm_instance = TaskBaseLSTM(vocab_size=..., emb_dim=..., hidden_dim=...)
    #
    # Not initializing the actual model yet to avoid errors before it's ready.
    return


def model0_base_lstm_predict(history: List[str], question: str) -> str:
    """
    Base LSTM (no memory augmentation) evaluation interface.

    Key point: use BaseMemoryLSTM.prepare_input_text(history, question)
               to align history into a single input string, then decode with LSTM.

    Currently a safe stub:
      - If you haven't connected the actual LSTM yet, return a fixed sentence
      - Later replace the TODO section with real decoding
    """
    init_base_lstm()

    if _base_lstm_instance is None:
        # No actual model yet → use as baseline stub
        return "adjust the user's study plan"

    # Example call to BaseMemoryLSTM's prepare_input_text
    input_text = _base_lstm_instance.prepare_input_text(history, question)

    # TODO: Convert input_text to token_ids → feed into LSTM → decode back to string
    # Example:
    #   ids = tokenizer.encode(input_text)
    #   logits = _base_lstm_instance(torch.tensor([ids]))
    #   pred_ids = decode_greedy(logits)
    #   return tokenizer.decode(pred_ids)
    #
    # Using placeholder for now to avoid breaking before model training:
    return "adjust the user's study plan"


# ============== Four memory-augmented stub models ==============


def model1_predict(history: List[str], question: str) -> str:
    """
    Model 1 stub: ignores history and doesn't understand question.
    Baseline: always return 'adjust the user's study plan'
    (later replace with Summarization-only LSTM)
    """
    return "adjust the user's study plan"


def model2_predict(history: List[str], question: str) -> str:
    """
    Model 2 stub: simple keyword-based.
    Future: replace with summarization + token limit LSTM.
    """
    q = normalize_text(question)

    if "target role" in q or "change my target role" in q or "aim for a" in q:
        return "update the user's target role"
    if "weekly" in q or "hours" in q or "schedule" in q:
        return "update the user's weekly study hours"
    if "pause" in q or "stop my study plan" in q or "on hold" in q:
        return "pause the user's current study plan"
    if "resume" in q or "restart" in q or "reactivate" in q:
        return "resume the user's study plan"
    if "reset" in q or "wipe my progress" in q or "clear my current progress" in q:
        return "reset the user's progress tracking"
    if "focus" in q or "change my main focus" in q:
        return "change the main focus area of the study plan"
    if "recommend" in q or "suggest" in q or "what i should learn next" in q:
        return "provide new learning recommendations for the user"

    # Default fallback
    return "adjust the user's study plan"


def model3_predict(history: List[str], question: str) -> str:
    """
    Model 3 stub: uses history:
      - If history contains a very similar question, return that task_summary.
    Simulates simple baseline with "some memory".
    Future: replace with Sum + token + NER LSTM.
    """
    q_norm = normalize_text(question)

    for ctx in reversed(history):
        # ctx: "user X: request => task_summary"
        if "=>" in ctx:
            req_part, summary_part = ctx.split("=>", 1)
            req_norm = normalize_text(req_part)
            if text_similarity(q_norm, req_norm) >= 0.9:
                return summary_part.strip()

    # No similar match found, fall back to keyword heuristic
    return model2_predict(history, question)


def model4_predict(history: List[str], question: str) -> str:
    """
    Model 4 stub: stronger "full memory" baseline.
    Future: replace with Full (semantic memory + NER + STM/LTM) LSTM.

    - Search history for similar requests; if similarity >= 0.8, use its summary.
    - Otherwise fall back to keyword heuristic.
    """
    q_norm = normalize_text(question)

    best_sim = 0.0
    best_summary = None

    for ctx in history:
        if "=>" in ctx:
            req_part, summary_part = ctx.split("=>", 1)
            req_norm = normalize_text(req_part)
            sim = text_similarity(q_norm, req_norm)
            if sim > best_sim:
                best_sim = sim
                best_summary = summary_part.strip()

    if best_summary is not None and best_sim >= 0.8:
        return best_summary

    return model2_predict(history, question)


# ============== main ==============


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(
        current_dir, "data", "task_oriented_skillminer_synthetic.csv"
    )

    print(f"Loading task dataset from: {csv_path}")
    data = load_task_csv(csv_path)

    models = [
        TaskModelWrapper("BaseLSTM_NoMemory", model0_base_lstm_predict),
        TaskModelWrapper("TaskModel_1_AlwaysAdjust", model1_predict),
        TaskModelWrapper("TaskModel_2_KeywordHeuristic", model2_predict),
        TaskModelWrapper("TaskModel_3_HistoryExactMatch", model3_predict),
        TaskModelWrapper("TaskModel_4_FullMemoryHistory", model4_predict),
    ]

    for m in models:
        evaluate_task_model(m, data, history_size=20, sim_threshold=0.7)


if __name__ == "__main__":
    main()
