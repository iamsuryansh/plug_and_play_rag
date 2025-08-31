from typing import List, Dict, Any
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """Manages chat history for users."""
    
    def __init__(self, history_dir: str = "./chat_history"):
        self.history_dir = history_dir
        self._ensure_history_dir()
    
    def _ensure_history_dir(self) -> None:
        """Ensure chat history directory exists."""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            logger.info(f"Created chat history directory: {self.history_dir}")
    
    def _get_user_history_file(self, user_name: str) -> str:
        """Get the file path for a user's chat history."""
        # Sanitize user_name for filename
        safe_name = "".join(c for c in user_name if c.isalnum() or c in ('-', '_'))
        return os.path.join(self.history_dir, f"{safe_name}_history.json")
    
    async def add_message(
        self,
        user_name: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add a message to user's chat history.
        
        Args:
            user_name: User identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Additional metadata (e.g., sources, timestamp)
        """
        try:
            history_file = self._get_user_history_file(user_name)
            
            # Load existing history
            history = await self._load_history(history_file)
            
            # Create new message
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Add to history
            history.append(message)
            
            # Keep only last 100 messages to prevent unlimited growth
            if len(history) > 100:
                history = history[-100:]
            
            # Save updated history
            await self._save_history(history_file, history)
            
            logger.debug(f"Added {role} message to history for user: {user_name}")
            
        except Exception as e:
            logger.error(f"Error adding message to chat history: {e}")
            # Don't raise exception as chat history is not critical
    
    async def get_history(
        self,
        user_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a user.
        
        Args:
            user_name: User identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of chat messages
        """
        try:
            history_file = self._get_user_history_file(user_name)
            history = await self._load_history(history_file)
            
            # Return last N messages
            return history[-limit:] if history else []
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def clear_history(self, user_name: str) -> None:
        """Clear chat history for a user."""
        try:
            history_file = self._get_user_history_file(user_name)
            if os.path.exists(history_file):
                os.remove(history_file)
                logger.info(f"Cleared chat history for user: {user_name}")
            
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
            raise
    
    async def _load_history(self, history_file: str) -> List[Dict[str, Any]]:
        """Load chat history from file."""
        if not os.path.exists(history_file):
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not load history file: {history_file}")
            return []
    
    async def _save_history(
        self,
        history_file: str,
        history: List[Dict[str, Any]]
    ) -> None:
        """Save chat history to file."""
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
