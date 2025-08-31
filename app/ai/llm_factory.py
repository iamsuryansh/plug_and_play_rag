from typing import Optional, Dict, Any
import logging
from ..config import settings
from .base_client import BaseLLMClient
from .gemini_client import GeminiClient
from .custom_llm_client import create_custom_llm_client

logger = logging.getLogger(__name__)

class LLMFactory:
    """Factory for creating LLM clients based on configuration."""
    
    @staticmethod
    def create_client(
        provider: str = "gemini",
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        Create an LLM client based on the specified provider.
        
        Args:
            provider: LLM provider ("gemini", "ollama", "lmstudio", "openai-compatible", "custom")
            model_name: Model name to use
            api_key: API key (if required)
            endpoint_url: API endpoint URL (for custom providers)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Configured LLM client
        
        Raises:
            ValueError: If required parameters are missing or provider is unsupported
        """
        provider = provider.lower()
        
        if provider == "gemini":
            api_key = api_key or settings.GEMINI_API_KEY
            if not api_key:
                raise ValueError("Gemini API key is required")
            return GeminiClient(api_key=api_key)
        
        elif provider in ["ollama", "lmstudio", "openai-compatible", "custom"]:
            if not model_name:
                # Set default model names for different providers
                if provider == "ollama":
                    model_name = "llama2"
                elif provider == "lmstudio":
                    model_name = "local-model"
                else:
                    raise ValueError(f"model_name is required for {provider}")
            
            return create_custom_llm_client(
                provider=provider,
                model_name=model_name,
                endpoint_url=endpoint_url,
                api_key=api_key,
                **kwargs
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> BaseLLMClient:
        """
        Create an LLM client from a configuration dictionary.
        
        Args:
            config: Configuration dictionary with provider settings
            
        Example config:
            {
                "provider": "ollama",
                "model_name": "llama2",
                "endpoint_url": "http://localhost:11434"
            }
        """
        return LLMFactory.create_client(**config)
    
    @staticmethod
    def get_supported_providers() -> Dict[str, Dict[str, Any]]:
        """Get information about supported providers."""
        return {
            "gemini": {
                "description": "Google Gemini AI",
                "requires_api_key": True,
                "requires_endpoint": False,
                "default_models": ["gemini-pro", "gemini-pro-vision"]
            },
            "ollama": {
                "description": "Ollama local LLM server",
                "requires_api_key": False,
                "requires_endpoint": False,
                "default_endpoint": "http://localhost:11434",
                "default_models": ["llama2", "codellama", "mistral", "neural-chat"]
            },
            "lmstudio": {
                "description": "LM Studio local server",
                "requires_api_key": False,
                "requires_endpoint": False,
                "default_endpoint": "http://localhost:1234",
                "default_models": ["local-model"]
            },
            "openai-compatible": {
                "description": "OpenAI-compatible API (Together, Anyscale, etc.)",
                "requires_api_key": True,
                "requires_endpoint": True,
                "examples": [
                    "https://api.together.xyz/v1/chat/completions",
                    "https://api.endpoints.anyscale.com/v1/chat/completions"
                ]
            },
            "custom": {
                "description": "Custom API endpoint with configurable request/response format",
                "requires_api_key": False,
                "requires_endpoint": True,
                "configurable": True
            }
        }
