from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_response_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM."""
        pass
    
    @abstractmethod
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the LLM client."""
        pass
