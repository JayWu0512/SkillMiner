"""
Short-Term Memory (STM) module for recent conversation summarization.
STM maintains a condensed representation of recent conversations using summarization
and token limit control.
"""
from typing import List, Dict, Optional, Tuple
from transformers import pipeline, AutoTokenizer
from src.core.config import STM_MAX_MESSAGES, STM_MAX_TOKENS, SUMMARIZATION_MODEL
import re
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


class TokenLimitController:
    """Manages token limits for STM summaries."""

    def __init__(self, max_tokens: int = STM_MAX_TOKENS):
        self.max_tokens = max_tokens
        self.tokenizer = None  # lazily loaded

    # ---- internal helpers ----

    def _ensure_tokenizer(self) -> None:
        """
        Lazily load a tokenizer based on the summarization model.

        If loading fails for any reason, we leave tokenizer as None and fall
        back to the simple char-based heuristic.
        """
        if self.tokenizer is not None:
            return
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(SUMMARIZATION_MODEL)
        except Exception:
            # Fall back to heuristic mode
            self.tokenizer = None

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.

        - If HF tokenizer is available, use real token count.
        - Otherwise, fall back to rough heuristic (~4 chars/token).
        """
        if not text:
            return 0

        self._ensure_tokenizer()
        if self.tokenizer is not None:
            try:
                ids = self.tokenizer.encode(text, add_special_tokens=False)
                return len(ids)
            except Exception:
                # If something goes wrong mid-run, fall back to heuristic
                pass

        # Fallback heuristic
        return len(text) // 4

    # ---- public API ----

    def truncate(self, text: str, max_tokens: int | None = None) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens (uses self.max_tokens if None)

        Returns:
            Truncated text
        """
        if not text:
            return ""

        if max_tokens is None:
            max_tokens = self.max_tokens

        # Try tokenizer-based truncation first
        self._ensure_tokenizer()
        if self.tokenizer is not None:
            try:
                ids = self.tokenizer.encode(text, add_special_tokens=False)
                if len(ids) <= max_tokens:
                    return text

                truncated_ids = ids[:max_tokens]
                truncated_text = self.tokenizer.decode(
                    truncated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
                )
                return truncated_text.strip() + "..."
            except Exception:
                # If tokenizer fails, fall back to char-based heuristic
                pass

        # Fallback: char-based heuristic (~4 chars per token)
        estimated_tokens = len(text) // 4
        if estimated_tokens <= max_tokens:
            return text

        max_chars = max_tokens * 4
        truncated = text[:max_chars]

        # Try to truncate at sentence boundary
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")
        cutoff = max(last_period, last_newline)

        if cutoff > max_chars * 0.8:  # Only use boundary if it's not too short
            return truncated[: cutoff + 1]

        return truncated + "..."

    def compress(self, text: str, target_tokens: int) -> str:
        """
        Compress text to the target token count using a simple strategy.

        Current behavior: if the text exceeds target_tokens, first truncate it
        to roughly 2×target_tokens to leave some buffer, and then let the
        upper-level summarizer (ShortTermMemory.summarizer) perform a finer
        summary/compression.

        Args:
            text: Text to compress
            target_tokens: Target token count

        Returns:
            Compressed text
        """
        if self._estimate_tokens(text) <= target_tokens:
            return text

        # Do a rough compression first, leave buffer for the summarizer
        truncated = self.truncate(text, target_tokens * 2)
        return truncated


class SummarizationLayer:
    """Summarization layer using pre-trained models."""

    def __init__(self, model_name: str = SUMMARIZATION_MODEL):
        self.model_name = model_name
        self.summarizer = None
        self.tokenizer = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the summarization model."""
        try:
            # Using a smaller summarization model is usually faster.
            if "bart-large" in self.model_name.lower():
                try:
                    self.summarizer = pipeline(
                        "summarization", model=self.model_name, device=-1  # CPU
                    )
                except Exception:
                    # If the specified large model fails, fall back to a common bart-large-cnn
                    self.summarizer = pipeline(
                        "summarization", model="facebook/bart-large-cnn", device=-1
                    )
            else:
                self.summarizer = pipeline(
                    "summarization", model=self.model_name, device=-1
                )

            # Tokenizer is mainly used if you want finer control over input length later
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception as e:
            print(f"[STM] Warning: Could not load summarization model {self.model_name}: {e}")
            print("[STM] Falling back to extractive summarization")
            self.summarizer = None
            self.tokenizer = None

    def summarize(
        self,
        text: str,
        max_length: int | None = None,
        min_length: int | None = None,
    ) -> str:
        """
        Summarize text using pre-trained model.

        Args:
            text: Text to summarize
            max_length: Maximum summary length (in tokens/words, depends on model)
            min_length: Minimum summary length

        Returns:
            Summarized text
        """
        if not text or not text.strip():
            return ""

        # If the summarization model failed to load, use simple extractive summarization
        if self.summarizer is None:
            return self._extractive_summarize(text, max_length or STM_MAX_TOKENS)

        try:
            # Basic length control: if not specified, use STM_MAX_TOKENS as upper bound
            if max_length is None:
                # Heuristic: don't let summary exceed half of the original text and cap by STM_MAX_TOKENS
                max_length = min(STM_MAX_TOKENS, max(32, len(text.split()) // 2))
            if min_length is None:
                min_length = max(10, max_length // 4)

            # Control input length to avoid exceeding model max input (most are ~1024 tokens)
            max_input_words = 1024
            words = text.split()
            if len(words) > max_input_words:
                text = " ".join(words[:max_input_words])

            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
            )
            if isinstance(result, list) and result:
                summary = result[0].get("summary_text", text)
            else:
                summary = result.get("summary_text", text)
            return summary
        except Exception as e:
            print(f"[STM] Error in summarization: {e}")
            # Fallback to extractive summarization
            return self._extractive_summarize(text, max_length or STM_MAX_TOKENS)

    def _extractive_summarize(self, text: str, max_sentences: int = 5) -> str:
        """
        Simple extractive summarization as fallback.
        Takes first N sentences.

        Args:
            text: Text to summarize
            max_sentences: Maximum number of sentences to keep

        Returns:
            Extracted summary
        """
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return text
        return ". ".join(sentences[:max_sentences]) + "."


class ShortTermMemory:
    """
    Short-Term Memory manager for recent conversation context.
    Maintains in-memory summaries of recent messages.
    """

    def __init__(
        self,
        user_id: str,
        max_messages: int = STM_MAX_MESSAGES,
        max_tokens: int = STM_MAX_TOKENS,
    ):
        self.user_id = user_id
        self.max_messages = max_messages
        self.max_tokens = max_tokens

        self.summarizer = SummarizationLayer()
        self.token_controller = TokenLimitController(max_tokens)

        # In-memory storage: list of (role, content) tuples
        self.recent_messages: List[Tuple[str, str]] = []
        self.summary: str = ""

    # ---- mutation ----

    def add_message(self, role: str, content: str):
        """
        Add a new message to STM.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if not content or not content.strip():
            return

        self.recent_messages.append((role, content))

        # Keep only last N messages
        if len(self.recent_messages) > self.max_messages:
            self.recent_messages = self.recent_messages[-self.max_messages :]

        # Update summary
        self._update_summary()

    def _update_summary(self):
        """Update the STM summary from recent messages."""
        if not self.recent_messages:
            self.summary = ""
            return

        # Format messages as conversation
        conversation_text = self._format_conversation()

        # Decide whether to run summarization based on token count
        estimated_tokens = self.token_controller._estimate_tokens(conversation_text)

        if estimated_tokens > self.max_tokens:
            # Summarize the conversation
            rough_summary = self.summarizer.summarize(
                conversation_text, max_length=self.max_tokens
            )
            self.summary = self.token_controller.truncate(rough_summary, self.max_tokens)
        else:
            # Use conversation as-is if it fits
            self.summary = self.token_controller.truncate(conversation_text, self.max_tokens)

    def _format_conversation(self) -> str:
        """Format recent messages as a conversation string."""
        formatted: List[str] = []
        for role, content in self.recent_messages:
            role_label = "User" if role == "user" else "Assistant"
            formatted.append(f"{role_label}: {content}")
        return "\n\n".join(formatted)

    # ---- accessors ----

    def get_summary(self) -> str:
        """
        Get the current STM summary.

        Returns:
            STM summary string
        """
        return self.summary

    def clear(self):
        """Clear STM (useful for new sessions)."""
        self.recent_messages = []
        self.summary = ""

    def get_recent_messages(self, n: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        Get recent messages.

        Args:
            n: Number of messages to retrieve (None for all)

        Returns:
            List of (role, content) tuples
        """
        if n is None:
            return self.recent_messages.copy()
        return self.recent_messages[-n:] if n > 0 else []


# Global STM storage (in-memory, per user)
_stm_storage: Dict[str, ShortTermMemory] = {}


def get_stm(user_id: str) -> ShortTermMemory:
    """
    Get or create STM for a user.

    Args:
        user_id: User ID

    Returns:
        ShortTermMemory instance for the user
    """
    if user_id not in _stm_storage:
        _stm_storage[user_id] = ShortTermMemory(user_id)
    return _stm_storage[user_id]


def clear_stm(user_id: str):
    """Clear STM for a user."""
    if user_id in _stm_storage:
        _stm_storage[user_id].clear()
