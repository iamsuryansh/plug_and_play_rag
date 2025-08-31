import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any, Optional, List
import httpx

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class CustomLLMClient(BaseLLMClient):
    """
    Generic LLM client that can work with any OpenAI-compatible API endpoint.
    Supports local LLMs like Ollama, LM Studio, or custom API servers.
    """
    
    def __init__(
        self,
        endpoint_url: str,
        model_name: str = "default",
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        request_template: Optional[Dict[str, Any]] = None,
        response_path: str = "choices.0.message.content",
        stream_response_path: str = "choices.0.delta.content",
        timeout: int = 60
    ):
        """
        Initialize the custom LLM client.
        
        Args:
            endpoint_url: The API endpoint URL (e.g., http://localhost:11434/v1/chat/completions)
            model_name: Model identifier
            api_key: Optional API key for authentication
            custom_headers: Additional headers to include in requests
            request_template: Custom request body template
            response_path: JSONPath to extract response content (dot-separated)
            stream_response_path: JSONPath to extract streaming response content
            timeout: Request timeout in seconds
        """
        self.endpoint_url = endpoint_url.rstrip('/')
        self.model_name = model_name
        self.api_key = api_key
        self.timeout = timeout
        
        # Set up headers
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        if custom_headers:
            self.headers.update(custom_headers)
        
        # Default OpenAI-compatible request template
        self.request_template = request_template or {
            "model": model_name,
            "messages": [],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        self.response_path = response_path.split('.')
        self.stream_response_path = stream_response_path.split('.')
        
        logger.info(f"Custom LLM client initialized for {endpoint_url} with model {model_name}")
    
    def _extract_from_response(self, response_data: Dict, path: List[str]) -> Optional[str]:
        """Extract content from response using JSONPath."""
        try:
            current = response_data
            for key in path:
                if key.isdigit():
                    current = current[int(key)]
                else:
                    current = current[key]
            return current
        except (KeyError, IndexError, TypeError):
            return None
    
    def _build_request_body(self, prompt: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Build the request body based on the template."""
        request_body = self.request_template.copy()
        
        # Handle messages format (OpenAI style)
        if "messages" in request_body:
            request_body["messages"] = [
                {"role": "user", "content": prompt}
            ]
        else:
            # Fallback for non-OpenAI APIs
            request_body["prompt"] = prompt
        
        # Add streaming flag
        request_body["stream"] = stream
        
        # Override with any custom parameters
        request_body.update(kwargs)
        
        return request_body
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a non-streaming response."""
        try:
            request_body = self._build_request_body(prompt, stream=False, **kwargs)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint_url,
                    json=request_body,
                    headers=self.headers
                )
                response.raise_for_status()
                
                response_data = response.json()
                content = self._extract_from_response(response_data, self.response_path)
                
                if content is None:
                    logger.error(f"Could not extract content from response: {response_data}")
                    return "Error: Could not parse LLM response"
                
                return content
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling custom LLM: {e}")
            raise Exception(f"LLM API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating response with custom LLM: {e}")
            raise Exception(f"LLM generation failed: {str(e)}")
    
    async def generate_response_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Generate a streaming response."""
        try:
            request_body = self._build_request_body(prompt, stream=True, **kwargs)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    self.endpoint_url,
                    json=request_body,
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                content = self._extract_from_response(data, self.stream_response_path)
                                
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in streaming response: {e}")
            yield f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about this client."""
        return {
            "type": "custom_llm",
            "endpoint_url": self.endpoint_url,
            "model_name": self.model_name,
            "has_api_key": bool(self.api_key),
            "headers": {k: ("***" if "auth" in k.lower() else v) for k, v in self.headers.items()},
            "request_template": self.request_template
        }


class OllamaClient(CustomLLMClient):
    """Specialized client for Ollama local LLM server."""
    
    def __init__(
        self,
        model_name: str = "llama2",
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        endpoint_url = f"{base_url}/v1/chat/completions"
        super().__init__(
            endpoint_url=endpoint_url,
            model_name=model_name,
            request_template={
                "model": model_name,
                "messages": [],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            **kwargs
        )


class LMStudioClient(CustomLLMClient):
    """Specialized client for LM Studio local server."""
    
    def __init__(
        self,
        model_name: str = "local-model",
        base_url: str = "http://localhost:1234",
        **kwargs
    ):
        endpoint_url = f"{base_url}/v1/chat/completions"
        super().__init__(
            endpoint_url=endpoint_url,
            model_name=model_name,
            **kwargs
        )


class OpenAICompatibleClient(CustomLLMClient):
    """Client for OpenAI-compatible APIs (e.g., Together AI, Anyscale, etc.)."""
    
    def __init__(
        self,
        endpoint_url: str,
        model_name: str,
        api_key: str,
        **kwargs
    ):
        super().__init__(
            endpoint_url=endpoint_url,
            model_name=model_name,
            api_key=api_key,
            **kwargs
        )


# Factory function for easy client creation
def create_custom_llm_client(
    provider: str,
    model_name: str,
    endpoint_url: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMClient:
    """
    Factory function to create LLM clients based on provider.
    
    Args:
        provider: Provider type ("ollama", "lmstudio", "openai-compatible", "custom")
        model_name: Model identifier
        endpoint_url: API endpoint URL (required for some providers)
        api_key: API key (if required)
        **kwargs: Additional client parameters
    
    Returns:
        Configured LLM client
    """
    provider = provider.lower()
    
    if provider == "ollama":
        base_url = endpoint_url or "http://localhost:11434"
        return OllamaClient(model_name=model_name, base_url=base_url, **kwargs)
    
    elif provider == "lmstudio":
        base_url = endpoint_url or "http://localhost:1234"
        return LMStudioClient(model_name=model_name, base_url=base_url, **kwargs)
    
    elif provider == "openai-compatible":
        if not endpoint_url:
            raise ValueError("endpoint_url is required for openai-compatible provider")
        if not api_key:
            raise ValueError("api_key is required for openai-compatible provider")
        return OpenAICompatibleClient(
            endpoint_url=endpoint_url,
            model_name=model_name,
            api_key=api_key,
            **kwargs
        )
    
    elif provider == "custom":
        if not endpoint_url:
            raise ValueError("endpoint_url is required for custom provider")
        return CustomLLMClient(
            endpoint_url=endpoint_url,
            model_name=model_name,
            api_key=api_key,
            **kwargs
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}. Supported: ollama, lmstudio, openai-compatible, custom")
