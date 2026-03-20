"""
Memory Service for KINGPARTHH Bot
Manages conversation history and user memory using SQLite.
"""

from typing import List, Dict, Any
from database import db


class MemoryService:
    """
    Service for managing conversation memory.
    Stores and retrieves user conversation history.
    """
    
    def __init__(self, max_messages: int = 5):
        """
        Initialize the memory service.
        
        Args:
            max_messages: Maximum number of messages to store per user
        """
        self.max_messages = max_messages
    
    def add_message(self, user_id: int, role: str, content: str):
        """
        Add a message to user's conversation history.
        
        Args:
            user_id: Telegram user ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        db.add_message(user_id, role, content)
        
        # Keep only the last N messages
        self._prune_messages(user_id)
    
    def _prune_messages(self, user_id: int):
        """
        Remove old messages beyond the limit.
        
        Args:
            user_id: Telegram user ID
        """
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Delete old messages beyond the limit
        cursor.execute('''
            DELETE FROM user_messages 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM user_messages 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            )
        ''', (user_id, user_id, self.max_messages))
        
        conn.commit()
        conn.close()
    
    def get_conversation(self, user_id: int) -> List[Dict[str, str]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            List of message dictionaries
        """
        return db.get_conversation_history(user_id, self.max_messages)
    
    def clear_memory(self, user_id: int):
        """
        Clear user's conversation history.
        
        Args:
            user_id: Telegram user ID
        """
        db.clear_conversation(user_id)
    
    def get_context_string(self, user_id: int) -> str:
        """
        Get conversation history as a string for AI prompts.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Formatted conversation context
        """
        history = self.get_conversation(user_id)
        
        if not history:
            return ""
        
        context_parts = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)


# Global memory service instance
memory_service = MemoryService()


def add_user_message(user_id: int, content: str):
    """Add a user message to memory."""
    memory_service.add_message(user_id, 'user', content)


def add_bot_message(user_id: int, content: str):
    """Add a bot message to memory."""
    memory_service.add_message(user_id, 'assistant', content)


def get_memory_context(user_id: int) -> str:
    """Get formatted memory context for AI."""
    return memory_service.get_context_string(user_id)


def clear_user_memory(user_id: int):
    """Clear user's conversation memory."""
    memory_service.clear_memory(user_id)
