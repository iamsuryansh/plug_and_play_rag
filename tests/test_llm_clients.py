"""
Unit tests for LLM Factory and clients
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.ai.llm_factory import LLMFactory
from app.ai.gemini_client import GeminiClient
from app.ai.custom_llm_client import CustomLLMClient, create_custom_llm_client


class TestLLMFactory:
    """Test LLM Factory functionality."""

    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = LLMFactory.get_supported_providers()
        
        assert "gemini" in providers
        assert "ollama" in providers
        assert "lmstudio" in providers
        assert "openai-compatible" in providers
        assert "custom" in providers
        
        # Check structure
        for provider_name, provider_info in providers.items():
            assert "description" in provider_info
            assert "requires_api_key" in provider_info
            assert "requires_endpoint" in provider_info

    @patch('app.ai.llm_factory.GeminiClient')
    def test_create_gemini_client(self, mock_gemini):
        """Test creating Gemini client."""
        mock_instance = Mock()
        mock_gemini.return_value = mock_instance
        
        client = LLMFactory.create_client(
            provider="gemini",
            api_key="test_key"
        )
        
        mock_gemini.assert_called_once_with(api_key="test_key")
        assert client == mock_instance

    @patch('app.ai.llm_factory.create_custom_llm_client')
    def test_create_ollama_client(self, mock_create_custom):
        """Test creating Ollama client."""
        mock_client = Mock()
        mock_create_custom.return_value = mock_client
        
        client = LLMFactory.create_client(
            provider="ollama",
            model_name="llama2"
        )
        
        mock_create_custom.assert_called_once_with(
            provider="ollama",
            model_name="llama2",
            endpoint_url=None,
            api_key=None
        )
        assert client == mock_client

    def test_create_client_invalid_provider(self):
        """Test creating client with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMFactory.create_client(provider="invalid_provider")

    def test_create_from_config(self):
        """Test creating client from configuration dictionary."""
        config = {
            "provider": "ollama",
            "model_name": "llama2",
            "endpoint_url": "http://localhost:11434"
        }
        
        with patch.object(LLMFactory, 'create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            client = LLMFactory.create_from_config(config)
            
            mock_create.assert_called_once_with(**config)
            assert client == mock_client


class TestGeminiClient:
    """Test Gemini client functionality."""

    @patch('app.ai.gemini_client.genai')
    def test_gemini_client_initialization(self, mock_genai):
        """Test Gemini client initialization."""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient(api_key="test_key")
        
        mock_genai.configure.assert_called_once_with(api_key="test_key")
        assert client.model == mock_model

    def test_gemini_client_get_info(self):
        """Test getting client info."""
        with patch('app.ai.gemini_client.genai'):
            client = GeminiClient(api_key="test_key")
            info = client.get_client_info()
            
            assert info["type"] == "gemini"
            assert "model" in info
            assert "temperature" in info
            assert "max_tokens" in info
            assert info["has_api_key"] is True

    @patch('app.ai.gemini_client.genai')
    @pytest.mark.asyncio
    async def test_gemini_generate_response(self, mock_genai):
        """Test generating response with Gemini."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Generated response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient(api_key="test_key")
        response = await client.generate_response(
            question="Test question",
            context_documents=[{"content": "Test context"}]
        )
        
        assert response == "Generated response"
        mock_model.generate_content.assert_called_once()


class TestCustomLLMClient:
    """Test custom LLM client functionality."""

    def test_custom_client_initialization(self):
        """Test custom client initialization."""
        client = CustomLLMClient(
            endpoint_url="http://localhost:8080/chat",
            model_name="test-model"
        )
        
        assert client.endpoint_url == "http://localhost:8080/chat"
        assert client.model_name == "test-model"
        assert client.headers["Content-Type"] == "application/json"

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_custom_client_generate_response(self, mock_post):
        """Test generating response with custom client."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        client = CustomLLMClient(
            endpoint_url="http://localhost:8080/chat",
            model_name="test-model"
        )
        
        response = await client.generate_response(
            prompt="Test prompt"
        )
        
        assert response == "Test response"
        mock_post.assert_called_once()

    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        client = create_custom_llm_client(
            provider="ollama",
            model_name="llama2"
        )
        
        assert client.endpoint_url == "http://localhost:11434/v1/chat/completions"
        assert client.model_name == "llama2"

    def test_create_lmstudio_client(self):
        """Test creating LM Studio client."""
        client = create_custom_llm_client(
            provider="lmstudio",
            model_name="local-model"
        )
        
        assert client.endpoint_url == "http://localhost:1234/v1/chat/completions"
        assert client.model_name == "local-model"

    def test_create_openai_compatible_client(self):
        """Test creating OpenAI-compatible client."""
        client = create_custom_llm_client(
            provider="openai-compatible",
            model_name="gpt-4",
            endpoint_url="https://api.example.com/v1/chat/completions",
            api_key="test-key"
        )
        
        assert client.endpoint_url == "https://api.example.com/v1/chat/completions"
        assert client.model_name == "gpt-4"
        assert client.headers["Authorization"] == "Bearer test-key"

    def test_create_invalid_provider(self):
        """Test creating client with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_custom_llm_client(
                provider="invalid",
                model_name="test"
            )
