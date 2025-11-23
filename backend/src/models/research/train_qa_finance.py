"""
Train and evaluate LSTM memory model on Finance QA dataset.

This script is adapted from train_qa_memory.py to handle the finance.csv dataset.
Key differences:
- Uses "question" and "answer" columns from finance.csv
- Uses finance-specific NER (products, financial_terms, companies)
- Handles larger dataset (6k+ rows) with sampling per epoch
- Same training and testing approach as synthetic dataset

Usage:
    cd backend/src/models/research
    python train_qa_finance.py --epochs 5 --model_type full_memory --samples_per_epoch 200
"""

import argparse
import os
import csv
import difflib
import random
from typing import List, Tuple, Optional, Dict
import json

import torch
import torch.nn as nn
from torch.utils.data import Dataset

from openai import OpenAI  # Make sure OPENAI_API_KEY is set in env
from dotenv import load_dotenv
from pathlib import Path

from base_lstm_model import BaseMemoryLSTM
from model_0_base import BaseLSTM
from model_1_summarization import SummarizationOnlyLSTM
from model_2_sum_toklimit import SumTokenLimitLSTM
from model_3_sum_tok_ner import SumTokNerLSTM
from model_4_full_memory import FullMemoryLSTM

# Character-level tokenizer (same as train_qa_memory)
_PAD_CHAR = "<pad>"
_ALL_CHARS = [chr(i) for i in range(32, 127)]  # printable ASCII
_ITOS: List[str] = [_PAD_CHAR] + _ALL_CHARS
_STOI: Dict[str, int] = {ch: idx for idx, ch in enumerate(_ITOS)}
_VOCAB_SIZE = len(_ITOS)
_MAX_SEQ_LEN = 512

# Global OpenAI client
BASE_DIR = Path(__file__).resolve().parents[3]
env_path = BASE_DIR / ".env"
load_dotenv(env_path)
openai_client = OpenAI()


def encode_text(text: str) -> torch.Tensor:
    """Encode text into token ids."""
    text = text or ""
    text = text[:_MAX_SEQ_LEN]
    ids: List[int] = []
    for ch in text:
        ids.append(_STOI.get(ch, _STOI[" "]))
    if not ids:
        ids = [_STOI[" "]]
    return torch.tensor(ids, dtype=torch.long)  # (seq_len,)


def decode_ids(ids: List[int]) -> str:
    """Decode token ids back to text."""
    chars: List[str] = []
    for idx in ids:
        if 0 <= idx < len(_ITOS):
            ch = _ITOS[idx]
            if ch != _PAD_CHAR:
                chars.append(ch)
    return "".join(chars)


def normalize_text(text: str) -> str:
    """Normalize text for similarity comparison."""
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


def text_similarity(a: str, b: str) -> float:
    """Compute similarity score using difflib (0-1 range)."""
    return difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


# ==== Dataset ====


class QADataset(Dataset):
    """Dataset for QA pairs with history."""

    def __init__(
        self,
        rows: List[Tuple[int, str, str]],
        history_size: int = 20,
        cache_path: Optional[str] = None,
        model: Optional[BaseMemoryLSTM] = None,
    ):
        self.rows = rows
        self.history_size = history_size
        self.cache_path = cache_path
        self.model = model

        # Build history for each row
        self._histories: List[List[str]] = []
        history: List[str] = []
        for qa_id, q, a in rows:
            self._histories.append(history[-history_size:].copy())
            # Format as "Q: ...\nA: ..." for history
            history.append(f"Q: {q}\nA: {a}")

        # Optionally cache input texts
        self._cached_input_texts: Optional[List[str]] = None
        if cache_path and os.path.exists(cache_path):
            print(f"Loading cached input texts from {cache_path}...")
            with open(cache_path, "r", encoding="utf-8") as f:
                self._cached_input_texts = json.load(f)
            print(f"Loaded {len(self._cached_input_texts)} cached inputs.")
        elif model is not None:
            print("Pre-computing input texts (this happens once)...")
            self._cached_input_texts = []
            for i in range(len(self.rows)):
                if i % 20 == 0:
                    print(f"  Pre-computing {i}/{len(self.rows)}...")
                _, q, _ = self.rows[i]
                input_text = model.prepare_input_text(self._histories[i], q)
                self._cached_input_texts.append(input_text)

            if cache_path:
                os.makedirs(
                    os.path.dirname(cache_path) if os.path.dirname(cache_path) else ".",
                    exist_ok=True,
                )
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(self._cached_input_texts, f)
                print(f"Saved cached input texts to {cache_path}")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> Tuple[List[str], str, str, Optional[str]]:
        """Returns (history, question, answer, cached_input_text)."""
        _, q, a = self.rows[idx]
        history = self._histories[idx]
        cached_text = (
            self._cached_input_texts[idx] if self._cached_input_texts else None
        )
        return history, q, a, cached_text


def llm_judge_score(
    question: str,
    true_answer: str,
    pred_answer: str,
    model_name: str = "gpt-4o-mini",
) -> float:
    """
    Use an LLM as a judge to score how correct pred_answer is
    compared to true_answer in the context of question.

    Returns a float in [0, 1].
    Falls back to difflib similarity if LLM call fails.
    """
    if not true_answer and not pred_answer:
        return 1.0
    if not pred_answer:
        return 0.0

    prompt = f"""
You are grading a QA system.

Question:
{question}

Ground truth answer:
{true_answer}

Model answer:
{pred_answer}

Task:
Give a single numeric score between 0 and 1 indicating how semantically correct
the model answer is compared to the ground truth answer, where:
- 1 means fully correct (semantically equivalent),
- 0 means completely incorrect or unrelated.

Output ONLY the number, no explanation.
""".strip()

    try:
        resp = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict but fair evaluator for QA answers.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        text = (resp.choices[0].message.content or "").strip()
        score = float(text)
        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))
        return score
    except Exception as e:
        print(f"[LLM-JUDGE WARNING] Failed to score with LLM: {e}")
        # Fallback: use difflib similarity instead
        return text_similarity(pred_answer, true_answer)


def train_on_batch(
    model: BaseMemoryLSTM,
    history: List[str],
    question: str,
    target_answer: str,
    device: torch.device,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    cached_input: Optional[str] = None,
) -> float:
    """Train on a single QA pair using teacher forcing."""
    model.train()

    # Prepare input
    if cached_input is not None:
        input_text = cached_input
    else:
        input_text = model.prepare_input_text(history, question)

    # Encode input
    input_ids = encode_text(input_text).to(device)
    target_ids = encode_text(target_answer).to(device)

    # Create full sequence: input + target (for teacher forcing)
    full_seq = torch.cat([input_ids, target_ids], dim=0)
    batch_ids = full_seq.unsqueeze(0)

    optimizer.zero_grad()

    # Forward pass
    logits = model(batch_ids)

    # We want to predict target_ids given input_ids (next-token prediction)
    input_len = input_ids.size(0)
    target_len = target_ids.size(0)

    if input_len > 0:
        start_idx = input_len - 1
        end_idx = min(logits.size(1), input_len - 1 + target_len)

        if end_idx > start_idx:
            pred_logits = logits[0, start_idx:end_idx, :]

            # Ensure we have the right number of logits
            if pred_logits.size(0) < target_len:
                padding = pred_logits[-1:, :].repeat(target_len - pred_logits.size(0), 1)
                pred_logits = torch.cat([pred_logits, padding], dim=0)
            elif pred_logits.size(0) > target_len:
                pred_logits = pred_logits[:target_len, :]
        else:
            pred_logits = logits[0, -1:, :].repeat(target_len, 1)
    else:
        pred_logits = logits[0, :min(target_len, logits.size(1)), :]
        if pred_logits.size(0) < target_len:
            padding = pred_logits[-1:, :].repeat(target_len - pred_logits.size(0), 1)
            pred_logits = torch.cat([pred_logits, padding], dim=0)

    targets = target_ids[:pred_logits.size(0)]
    loss = criterion(pred_logits, targets)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    return loss.item()


@torch.no_grad()
def generate_answer(
    model: BaseMemoryLSTM,
    history: List[str],
    question: str,
    device: torch.device,
    max_length: int = 200,
    cached_input: Optional[str] = None,
) -> str:
    """Generate answer given history and question."""
    model.eval()

    if cached_input is not None:
        input_text = cached_input
    else:
        input_text = model.prepare_input_text(history, question)

    input_ids = encode_text(input_text).to(device)
    input_len = input_ids.size(0)

    max_input_len = 400
    if input_len > max_input_len:
        input_ids = input_ids[:max_input_len]
        input_len = max_input_len

    current_ids = input_ids.unsqueeze(0)
    generated: List[int] = []
    consecutive_spaces = 0
    max_consecutive_spaces = 10
    last_token = None
    repetition_count = 0
    max_repetition = 30
    last_3_tokens: List[int] = []

    for _ in range(max_length):
        if current_ids.size(1) > 600:
            current_ids = current_ids[:, -400:]

        logits = model(current_ids)
        last_logit = logits[0, -1, :]
        probs = torch.softmax(last_logit / 1.0, dim=-1)

        if repetition_count > 5:
            top_k = 5
            top_probs, top_indices = torch.topk(probs, top_k)
            top_probs = top_probs / top_probs.sum()
            idx_sample = int(torch.multinomial(top_probs, 1).item())
            next_id = int(top_indices[idx_sample].item())
        else:
            next_id = int(torch.argmax(last_logit).item())

        if next_id == _STOI[_PAD_CHAR]:
            break

        if len(last_3_tokens) >= 3:
            if generated[-2:] == last_3_tokens[-2:] and next_id == last_3_tokens[0]:
                repetition_count += 1
                if repetition_count >= max_repetition:
                    break
            elif next_id == last_token:
                repetition_count += 1
                if repetition_count >= max_repetition:
                    break
            else:
                repetition_count = 0
        elif next_id == last_token:
            repetition_count += 1
            if repetition_count >= max_repetition:
                break
        else:
            repetition_count = 0

        last_token = next_id
        last_3_tokens.append(next_id)
        if len(last_3_tokens) > 3:
            last_3_tokens.pop(0)

        generated.append(next_id)

        next_char = _ITOS[next_id] if 0 <= next_id < len(_ITOS) else " "
        if next_char == " ":
            consecutive_spaces += 1
            if consecutive_spaces >= max_consecutive_spaces and len(generated) > 50:
                while generated and _ITOS[generated[-1]] == " ":
                    generated.pop()
                break
        else:
            consecutive_spaces = 0

        next_tensor = torch.tensor([[next_id]], dtype=torch.long, device=device)
        current_ids = torch.cat([current_ids, next_tensor], dim=1)

    answer = decode_ids(generated)
    return answer.strip()


def test_memory(
    model: BaseMemoryLSTM,
    dataset: QADataset,
    test_indices: List[int],
    device: torch.device,
    sim_threshold: float = 0.6,
    debug: bool = False,
    max_gen_length: int = 300,
    return_similarities: bool = False,
    use_llm_judge: bool = True,
) -> Tuple[int, int, Optional[List[Tuple[float, float]]]]:
    """Test memory recall. Returns (correct, total, scores)."""
    correct = 0
    total = 0
    scores: Optional[List[Tuple[float, float]]] = [] if return_similarities else None

    for idx in test_indices:
        if idx < 0 or idx >= len(dataset):
            continue

        total += 1
        history, question, true_answer, cached_input = dataset[idx]

        pred_answer = generate_answer(
            model,
            history,
            question,
            device,
            cached_input=cached_input,
            max_length=max_gen_length,
        )

        llm_score = llm_judge_score(question, true_answer, pred_answer)
        difflib_score = text_similarity(pred_answer, true_answer)
        score = llm_score if use_llm_judge else difflib_score

        if return_similarities and scores is not None:
            scores.append((llm_score, difflib_score))

        if debug:
            print(f"\n  [DEBUG] Test idx={idx}")
            print(f"    Question: {question[:100]}...")
            print(f"    True answer: {true_answer[:100]}...")
            print(f"    Pred answer: {pred_answer[:200] if pred_answer else '(empty)'}")
            print(
                f"    LLM score: {llm_score:.4f}, "
                f"difflib score: {difflib_score:.4f} "
                f"(threshold: {sim_threshold}, using {'LLM-judge' if use_llm_judge else 'difflib'})"
            )
            print(f"    Success: {score >= sim_threshold}")

        if score >= sim_threshold:
            correct += 1

    if return_similarities:
        return correct, total, scores
    return correct, total, None


def load_finance_csv(path: str) -> List[Tuple[int, str, str]]:
    """Load Finance QA dataset from CSV."""
    rows: List[Tuple[int, str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, r in enumerate(reader):
            qa_id = idx  # Use index as ID
            q = r["question"]
            a = r["answer"]
            rows.append((qa_id, q, a))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Train QA memory LSTM on Finance dataset")
    parser.add_argument(
        "--model_type",
        type=str,
        default="full_memory",
        choices=["base", "summarization_only", "sum_token_limit", "sum_tok_ner", "full_memory"],
        help="Model type to train",
    )
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument(
        "--history_size",
        type=int,
        default=20,
        help="Number of previous Q&A pairs to keep in history",
    )
    parser.add_argument(
        "--checkpoint_dir",
        type=str,
        default="checkpoints_qa_finance",
        help="Directory to save checkpoints",
    )
    parser.add_argument(
        "--cache_dir",
        type=str,
        default="cache_qa_finance",
        help="Directory to cache pre-computed inputs",
    )
    parser.add_argument(
        "--stm_threshold",
        type=float,
        default=0.6,
        help="Score threshold for STM tests (0–1).",
    )
    parser.add_argument(
        "--ltm_threshold",
        type=float,
        default=0.5,
        help="Score threshold for LTM tests (0–1).",
    )
    parser.add_argument(
        "--samples_per_epoch",
        type=int,
        default=200,
        help="Number of samples to use per epoch (for large datasets)",
    )
    parser.add_argument(
        "--keep_cache",
        action="store_true",
        help="Keep existing cache instead of regenerating it",
    )
    parser.add_argument(
        "--emb_dim",
        type=int,
        default=256,
        help="Embedding dimension",
    )
    parser.add_argument(
        "--hidden_dim",
        type=int,
        default=256,
        help="Hidden dimension",
    )
    parser.add_argument(
        "--max_gen_length",
        type=int,
        default=300,
        help="Maximum generation length",
    )
    parser.add_argument(
        "--no_llm_judge",
        action="store_true",
        help="If set, disable LLM-as-a-judge and use difflib similarity instead.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="If set, suppress intermediate progress logs and only show epoch summaries.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling",
    )

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    os.makedirs(args.checkpoint_dir, exist_ok=True)
    os.makedirs(args.cache_dir, exist_ok=True)

    # Set random seed
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    # Load dataset
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "data", "finance.csv")
    
    # Verify file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Finance CSV file not found at: {csv_path}\n"
            f"Please ensure finance.csv exists in the data/ directory."
        )
    
    print(f"Loading dataset from: {csv_path}")
    all_rows = load_finance_csv(csv_path)
    print(f"Loaded {len(all_rows)} QA pairs")
    
    if len(all_rows) == 0:
        raise ValueError("No data loaded from CSV. Please check the file format.")

    # Build model
    vocab_size = _VOCAB_SIZE
    emb_dim = args.emb_dim
    hidden_dim = args.hidden_dim

    # Use finance domain for NER
    domain = "finance"

    if args.model_type == "base":
        model = BaseLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
    elif args.model_type == "summarization_only":
        model = SummarizationOnlyLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
    elif args.model_type == "sum_token_limit":
        model = SumTokenLimitLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim
        )
    elif args.model_type == "sum_tok_ner":
        model = SumTokNerLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim, domain=domain
        )
    elif args.model_type == "full_memory":
        model = FullMemoryLSTM(
            vocab_size=vocab_size, emb_dim=emb_dim, hidden_dim=hidden_dim, domain=domain
        )
    else:
        raise ValueError(f"Unknown model_type: {args.model_type}")

    model.to(device)

    # Pre-ingest history for semantic memory (if using FullMemoryLSTM)
    if isinstance(model, FullMemoryLSTM):
        print("Pre-ingesting history into semantic memory...")
        history_texts = []
        for _, q, a in all_rows:
            history_texts.append(f"Q: {q}\nA: {a}")
        model.ingest_history(history_texts)
        print("Done pre-ingesting history")

    # Setup training
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    use_llm_judge = not args.no_llm_judge
    print(f"\nTraining {args.model_type} on Finance dataset (device={device})")
    print(f"  Epochs: {args.epochs}")
    print(f"  Samples per epoch: {args.samples_per_epoch}")
    print(f"  History size: {args.history_size}")
    print(f"  STM threshold: {args.stm_threshold}")
    print(f"  LTM threshold: {args.ltm_threshold}")
    print(f"  Using LLM-as-a-judge: {use_llm_judge}")
    print(f"  Domain: {domain}")
    print()

    best_score = 0.0

    # Training loop
    for epoch in range(1, args.epochs + 1):
        print(f"\n{'=' * 60}")
        print(f"Epoch {epoch}/{args.epochs}")
        print(f"{'=' * 60}")

        # Sample rows for this epoch
        if len(all_rows) > args.samples_per_epoch:
            rows = random.sample(all_rows, args.samples_per_epoch)
            print(f"Using {len(rows)} sampled rows (from {len(all_rows)} total)")
        else:
            rows = all_rows

        # Create dataset for this epoch
        cache_path = os.path.join(args.cache_dir, f"{args.model_type}_epoch_{epoch}_inputs.json")

        if not args.keep_cache and os.path.exists(cache_path):
            print(f"Deleting old cache at {cache_path} to regenerate...")
            os.remove(cache_path)

        dataset = QADataset(
            rows,
            history_size=args.history_size,
            cache_path=cache_path,
            model=model,
        )

        total_loss = 0.0
        num_steps = 0

        # STM and LTM test tracking
        stm_test_indices: List[int] = []
        ltm_test_indices: List[int] = []
        stm_correct = 0
        stm_total = 0
        ltm_correct = 0
        ltm_total = 0
        stm_scores: List[Tuple[float, float]] = []
        ltm_scores: List[Tuple[float, float]] = []

        # Process rows sequentially
        for i in range(len(dataset)):
            history, question, answer, cached_input = dataset[i]

            # Train on this row
            loss = train_on_batch(
                model,
                history,
                question,
                answer,
                device,
                optimizer,
                criterion,
                cached_input=cached_input,
            )
            total_loss += loss
            num_steps += 1

            # STM test every 5 rows
            if (i + 1) % 5 == 0 and i >= 2:
                test_idx = i - 2
                stm_test_indices.append(test_idx)

            # LTM test every 10 rows
            if (i + 1) % 10 == 0 and i >= 9:
                test_idx = i - 9
                ltm_test_indices.append(test_idx)

            # Run tests periodically (every 10 training steps)
            if (i + 1) % 10 == 0:
                # Run STM tests
                if stm_test_indices:
                    stm_c, stm_t, stm_sims = test_memory(
                        model,
                        dataset,
                        stm_test_indices,
                        device,
                        sim_threshold=args.stm_threshold,
                        debug=(i + 1) == 10 and not args.quiet,
                        max_gen_length=args.max_gen_length,
                        return_similarities=True,
                        use_llm_judge=use_llm_judge,
                    )
                    stm_correct += stm_c
                    stm_total += stm_t
                    stm_scores.extend(stm_sims or [])
                    stm_test_indices = []

                # Run LTM tests
                if ltm_test_indices:
                    ltm_c, ltm_t, ltm_sims = test_memory(
                        model,
                        dataset,
                        ltm_test_indices,
                        device,
                        sim_threshold=args.ltm_threshold,
                        debug=(i + 1) == 10 and not args.quiet,
                        max_gen_length=args.max_gen_length,
                        return_similarities=True,
                        use_llm_judge=use_llm_judge,
                    )
                    ltm_correct += ltm_c
                    ltm_total += ltm_t
                    ltm_scores.extend(ltm_sims or [])
                    ltm_test_indices = []

                # Print progress
                avg_loss = total_loss / num_steps if num_steps > 0 else 0.0
                stm_acc = stm_correct / stm_total if stm_total > 0 else 0.0
                ltm_acc = ltm_correct / ltm_total if ltm_total > 0 else 0.0
                
                # Calculate average scores
                if stm_scores:
                    stm_avg_llm = sum(s[0] for s in stm_scores) / len(stm_scores)
                    stm_avg_difflib = sum(s[1] for s in stm_scores) / len(stm_scores)
                    stm_avg_score = stm_avg_llm if use_llm_judge else stm_avg_difflib
                else:
                    stm_avg_llm = 0.0
                    stm_avg_difflib = 0.0
                    stm_avg_score = 0.0
                
                if ltm_scores:
                    ltm_avg_llm = sum(s[0] for s in ltm_scores) / len(ltm_scores)
                    ltm_avg_difflib = sum(s[1] for s in ltm_scores) / len(ltm_scores)
                    ltm_avg_score = ltm_avg_llm if use_llm_judge else ltm_avg_difflib
                else:
                    ltm_avg_llm = 0.0
                    ltm_avg_difflib = 0.0
                    ltm_avg_score = 0.0

                if not args.quiet:
                    if (i + 1) % 50 == 0:
                        test_history, test_q, test_a, test_cached = dataset[i]
                        test_pred = generate_answer(
                            model,
                            test_history,
                            test_q,
                            device,
                            cached_input=test_cached,
                            max_length=args.max_gen_length,
                        )
                        print(
                            f"  Step {i+1}/{len(dataset)}: "
                            f"loss={avg_loss:.4f}, "
                            f"STM_acc={stm_acc:.3f} ({stm_correct}/{stm_total}) "
                            f"score_avg={stm_avg_score:.3f} (LLM={stm_avg_llm:.3f}/difflib={stm_avg_difflib:.3f}), "
                            f"LTM_acc={ltm_acc:.3f} ({ltm_correct}/{ltm_total}) "
                            f"score_avg={ltm_avg_score:.3f} (LLM={ltm_avg_llm:.3f}/difflib={ltm_avg_difflib:.3f})"
                        )
                        print(f"    Sample pred: {test_pred[:100]}...")
                    else:
                        print(
                            f"  Step {i+1}/{len(dataset)}: "
                            f"loss={avg_loss:.4f}, "
                            f"STM_acc={stm_acc:.3f} ({stm_correct}/{stm_total}) "
                            f"score_avg={stm_avg_score:.3f} (LLM={stm_avg_llm:.3f}/difflib={stm_avg_difflib:.3f}), "
                            f"LTM_acc={ltm_acc:.3f} ({ltm_correct}/{ltm_total}) "
                            f"score_avg={ltm_avg_score:.3f} (LLM={ltm_avg_llm:.3f}/difflib={ltm_avg_difflib:.3f})"
                        )

        # Final epoch summary
        avg_loss = total_loss / num_steps if num_steps > 0 else 0.0
        stm_acc = stm_correct / stm_total if stm_total > 0 else 0.0
        ltm_acc = ltm_correct / ltm_total if ltm_total > 0 else 0.0
        
        # Calculate statistics
        if stm_scores:
            stm_llm_scores = [s[0] for s in stm_scores]
            stm_difflib_scores = [s[1] for s in stm_scores]
            stm_avg_llm = sum(stm_llm_scores) / len(stm_llm_scores)
            stm_avg_difflib = sum(stm_difflib_scores) / len(stm_difflib_scores)
            stm_min_llm = min(stm_llm_scores)
            stm_max_llm = max(stm_llm_scores)
            stm_min_difflib = min(stm_difflib_scores)
            stm_max_difflib = max(stm_difflib_scores)
        else:
            stm_avg_llm = stm_avg_difflib = stm_min_llm = stm_max_llm = stm_min_difflib = stm_max_difflib = 0.0
        
        if ltm_scores:
            ltm_llm_scores = [s[0] for s in ltm_scores]
            ltm_difflib_scores = [s[1] for s in ltm_scores]
            ltm_avg_llm = sum(ltm_llm_scores) / len(ltm_llm_scores)
            ltm_avg_difflib = sum(ltm_difflib_scores) / len(ltm_difflib_scores)
            ltm_min_llm = min(ltm_llm_scores)
            ltm_max_llm = max(ltm_llm_scores)
            ltm_min_difflib = min(ltm_difflib_scores)
            ltm_max_difflib = max(ltm_difflib_scores)
        else:
            ltm_avg_llm = ltm_avg_difflib = ltm_min_llm = ltm_max_llm = ltm_min_difflib = ltm_max_difflib = 0.0

        print(f"\nEpoch {epoch} Summary:")
        print(f"  Average loss: {avg_loss:.4f}")
        print(
            f"  STM accuracy: {stm_acc:.3f} ({stm_correct}/{stm_total}) "
            f"[threshold: {args.stm_threshold}]"
        )
        print(
            f"    STM LLM score: avg={stm_avg_llm:.3f}, "
            f"min={stm_min_llm:.3f}, max={stm_max_llm:.3f}"
        )
        print(
            f"    STM difflib score: avg={stm_avg_difflib:.3f}, "
            f"min={stm_min_difflib:.3f}, max={stm_max_difflib:.3f}"
        )
        print(
            f"  LTM accuracy: {ltm_acc:.3f} ({ltm_correct}/{ltm_total}) "
            f"[threshold: {args.ltm_threshold}]"
        )
        print(
            f"    LTM LLM score: avg={ltm_avg_llm:.3f}, "
            f"min={ltm_min_llm:.3f}, max={ltm_max_llm:.3f}"
        )
        print(
            f"    LTM difflib score: avg={ltm_avg_difflib:.3f}, "
            f"min={ltm_min_difflib:.3f}, max={ltm_max_difflib:.3f}"
        )

        # Save checkpoint
        ckpt_path = os.path.join(
            args.checkpoint_dir, f"{args.model_type}_epoch_{epoch}.pt"
        )
        torch.save(model.state_dict(), ckpt_path)
        print(f"  Saved checkpoint to {ckpt_path}")

        # Save best model
        best_ckpt_path = os.path.join(
            args.checkpoint_dir, f"{args.model_type}_best.pt"
        )
        if epoch == 1 or (stm_acc + ltm_acc) > best_score:
            best_score = stm_acc + ltm_acc
            torch.save(model.state_dict(), best_ckpt_path)
            print(f"  Saved best model to {best_ckpt_path}")

    print("\nTraining complete!")


if __name__ == "__main__":
    main()

