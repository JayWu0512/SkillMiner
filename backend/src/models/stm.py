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
        self.tokenizer = None
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)."""
        return len(text) // 4
    
    def truncate(self, text: str, max_tokens: int = None) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens (uses self.max_tokens if None)
        
        Returns:
            Truncated text
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        estimated_tokens = self._estimate_tokens(text)
        if estimated_tokens <= max_tokens:
            return text
        
        # Truncate to approximately max_tokens
        max_chars = max_tokens * 4
        truncated = text[:max_chars]
        
        # Try to truncate at sentence boundary
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        cutoff = max(last_period, last_newline)
        
        if cutoff > max_chars * 0.8:  # Only use boundary if it's not too short
            return truncated[:cutoff + 1]
        
        return truncated + "..."
    
    def compress(self, text: str, target_tokens: int) -> str:
        """
        Compress text to target token count using summarization.
        
        Args:
            text: Text to compress
            target_tokens: Target token count
        
        Returns:
            Compressed text
        """
        if self._estimate_tokens(text) <= target_tokens:
            return text
        
        # If text is too long, truncate first then summarize
        # This is a simplified approach - in practice, you might want more sophisticated compression
        truncated = self.truncate(text, target_tokens * 2)  # Allow some buffer
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
            # Use a smaller model for faster inference
            # BART-large can be slow, so we'll use a smaller variant or T5
            if "bart-large" in self.model_name.lower():
                # Fallback to smaller model if large is too slow
                try:
                    self.summarizer = pipeline("summarization", model=self.model_name, device=-1)  # CPU
                except Exception:
                    # Fallback to smaller model
                    self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)
            else:
                self.summarizer = pipeline("summarization", model=self.model_name, device=-1)
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception as e:
            print(f"[STM] Warning: Could not load summarization model {self.model_name}: {e}")
            print("[STM] Falling back to extractive summarization")
            self.summarizer = None
    
    def summarize(self, text: str, max_length: int = None, min_length: int = None) -> str:
        """
        Summarize text using pre-trained model.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length (in tokens)
            min_length: Minimum summary length (in tokens)
        
        Returns:
            Summarized text
        """
        if not text or not text.strip():
            return ""
        
        # If model not available, use extractive summarization
        if self.summarizer is None:
            return self._extractive_summarize(text, max_length or STM_MAX_TOKENS)
        
        try:
            # Set default max_length if not provided
            if max_length is None:
                max_length = min(STM_MAX_TOKENS, len(text.split()) // 2)
            if min_length is None:
                min_length = max(10, max_length // 4)
            
            # Ensure text is not too long for the model
            # Most models have a max input length of 1024 tokens
            max_input_length = 1024
            if len(text.split()) > max_input_length:
                # Truncate to first max_input_length words
                words = text.split()[:max_input_length]
                text = " ".join(words)
            
            result = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            summary = result[0]['summary_text'] if isinstance(result, list) else result.get('summary_text', text)
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
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return '. '.join(sentences[:max_sentences]) + '.' if sentences else text


class ShortTermMemory:
    """
    Short-Term Memory manager for recent conversation context.
    Maintains in-memory summaries of recent messages.
    """
    
    def __init__(self, user_id: str, max_messages: int = STM_MAX_MESSAGES, max_tokens: int = STM_MAX_TOKENS):
        self.user_id = user_id
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        
        self.summarizer = SummarizationLayer()
        self.token_controller = TokenLimitController(max_tokens)
        
        # In-memory storage: list of (role, content) tuples
        self.recent_messages: List[Tuple[str, str]] = []
        self.summary: str = ""
    
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
            self.recent_messages = self.recent_messages[-self.max_messages:]
        
        # Update summary
        self._update_summary()
    
    def _update_summary(self):
        """Update the STM summary from recent messages."""
        if not self.recent_messages:
            self.summary = ""
            return
        
        # Format messages as conversation
        conversation_text = self._format_conversation()
        
        # Summarize if conversation is long
        estimated_tokens = self.token_controller._estimate_tokens(conversation_text)
        
        if estimated_tokens > self.max_tokens:
            # Summarize the conversation
            self.summary = self.summarizer.summarize(conversation_text, max_length=self.max_tokens)
        else:
            # Use conversation as-is if it fits
            self.summary = conversation_text
        
        # Ensure summary fits token limit
        self.summary = self.token_controller.truncate(self.summary, self.max_tokens)
    
    def _format_conversation(self) -> str:
        """Format recent messages as a conversation string."""
        formatted = []
        for role, content in self.recent_messages:
            role_label = "User" if role == "user" else "Assistant"
            formatted.append(f"{role_label}: {content}")
        return "\n\n".join(formatted)
    
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

