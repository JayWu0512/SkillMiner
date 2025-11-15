"""
Memory-Augmented Chat Service.
Orchestrates STM and LTM retrieval and integrates memory summaries with chat input.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid

from src.models.stm import get_stm, ShortTermMemory
from src.models.ltm import get_ltm, LongTermMemory
from src.db.supabase_client import get_supabase_client


class MemoryAugmentedChatService:
    """
    Service for managing memory-augmented chat context.
    Combines STM (recent context) and LTM (semantic/entity memory) with current input.
    """
    
    def __init__(self):
        self.supabase = None
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client."""
        try:
            self.supabase = get_supabase_client()
        except Exception as e:
            print(f"[MemoryChat] Warning: Could not initialize Supabase: {e}")
    
    def get_memory_context(self, user_id: str, current_message: str, 
                          resume_text: Optional[str] = None) -> Dict[str, str]:
        """
        Get memory-augmented context for current message.
        
        Args:
            user_id: User ID
            current_message: Current user message
            resume_text: Optional resume text for context
        
        Returns:
            Dictionary with 'stm_summary', 'ltm_summary', and 'combined_context'
        """
        print(f"[Memory] Building memory context for user: {user_id}")
        
        # Get STM summary
        stm = get_stm(user_id)
        stm_summary = stm.get_summary()
        print(f"[Memory] STM summary length: {len(stm_summary)} chars, messages: {len(stm.recent_messages)}")
        
        # Get LTM memories
        ltm = get_ltm()
        print(f"[Memory] Retrieving LTM memories for query: {current_message[:50]}...")
        ltm_memories = ltm.retrieve_memories(user_id, current_message)
        print(f"[Memory] Retrieved {len(ltm_memories)} LTM memories")
        ltm_summary = ltm.get_ltm_summary(ltm_memories)
        
        # Combine contexts
        context_parts = []
        
        if stm_summary:
            context_parts.append(f"Recent conversation summary:\n{stm_summary}")
            print(f"[Memory] STM context added ({len(stm_summary)} chars)")
        
        if ltm_summary:
            context_parts.append(f"Relevant past context:\n{ltm_summary}")
            print(f"[Memory] LTM context added ({len(ltm_summary)} chars)")
        
        combined_context = "\n\n".join(context_parts) if context_parts else ""
        print(f"[Memory] Combined context built: {len(combined_context)} total chars")
        
        return {
            "stm_summary": stm_summary,
            "ltm_summary": ltm_summary,
            "combined_context": combined_context
        }
    
    def update_memory(self, user_id: str, user_message: str, assistant_reply: str,
                     message_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Update STM and LTM after a conversation turn.
        
        Args:
            user_id: User ID
            user_message: User's message
            assistant_reply: Assistant's reply
            message_id: Optional message ID from database
        
        Returns:
            Tuple of (user_message_id, assistant_message_id) if stored in database
        """
        print(f"[Memory] Updating memory for user: {user_id}")
        
        # Update STM with new messages
        stm = get_stm(user_id)
        stm.add_message("user", user_message)
        print(f"[Memory] Added user message to STM ({len(user_message)} chars)")
        stm.add_message("assistant", assistant_reply)
        print(f"[Memory] Added assistant reply to STM ({len(assistant_reply)} chars)")
        
        # Store messages in database if Supabase is available
        user_msg_id = None
        assistant_msg_id = None
        
        if self.supabase is not None:
            try:
                # Store user message
                user_result = self.supabase.table("chat_messages").insert({
                    "id": message_id or str(uuid.uuid4()),
                    "user_id": user_id,
                    "role": "user",
                    "content": user_message,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                
                if user_result.data and len(user_result.data) > 0:
                    user_msg_id = user_result.data[0]["id"]
                
                # Store assistant message
                assistant_result = self.supabase.table("chat_messages").insert({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "role": "assistant",
                    "content": assistant_reply,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                
                if assistant_result.data and len(assistant_result.data) > 0:
                    assistant_msg_id = assistant_result.data[0]["id"]
                
                # Store in LTM (store both messages, but prioritize user message for NER)
                ltm = get_ltm()
                if user_msg_id:
                    print(f"[Memory] Storing user message in LTM (message_id: {user_msg_id})")
                    ltm_id = ltm.store_memory(user_id, user_msg_id, user_message)
                    if ltm_id:
                        print(f"[Memory] LTM memory stored successfully (id: {ltm_id})")
                    else:
                        print(f"[Memory] Warning: Failed to store LTM memory")
                if assistant_msg_id:
                    # Store assistant reply with lower priority (or skip if you prefer)
                    # ltm.store_memory(user_id, assistant_msg_id, assistant_reply)
                    pass
                
            except Exception as e:
                print(f"[MemoryChat] Error storing messages in database: {e}")
                import traceback
                print(traceback.format_exc())
        
        return user_msg_id, assistant_msg_id
    
    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get chat history from database.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        if self.supabase is None:
            return []
        
        try:
            result = self.supabase.table("chat_messages")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            
            if result.data:
                return result.data
            return []
        except Exception as e:
            print(f"[MemoryChat] Error retrieving chat history: {e}")
            return []
    
    def build_memory_augmented_input(self, user_id: str, current_message: str,
                                    resume_text: Optional[str] = None,
                                    rag_context: Optional[str] = None) -> str:
        """
        Build memory-augmented input string for LLM.
        
        Args:
            user_id: User ID
            current_message: Current user message
            resume_text: Optional resume text
            rag_context: Optional RAG context from retriever
        
        Returns:
            Formatted input string with all context
        """
        # Get memory context
        memory_context = self.get_memory_context(user_id, current_message, resume_text)
        
        # Build input parts
        parts = []
        
        # Resume context
        if resume_text:
            parts.append(f"Resume context:\n{resume_text[:4000]}")
        
        # RAG context
        if rag_context:
            parts.append(f"Relevant information:\n{rag_context}")
        
        # Memory context (STM + LTM)
        if memory_context["combined_context"]:
            parts.append(f"Conversation memory:\n{memory_context['combined_context']}")
        
        # Current message
        parts.append(f"Current question: {current_message}")
        
        return "\n\n".join(parts)
    
    def clear_user_memory(self, user_id: str):
        """
        Clear all memory for a user (STM only, LTM remains in database).
        
        Args:
            user_id: User ID
        """
        from src.models.stm import clear_stm
        clear_stm(user_id)


# Global service instance
_service_instance: Optional[MemoryAugmentedChatService] = None


def get_memory_chat_service() -> MemoryAugmentedChatService:
    """Get or create global memory chat service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MemoryAugmentedChatService()
    return _service_instance

