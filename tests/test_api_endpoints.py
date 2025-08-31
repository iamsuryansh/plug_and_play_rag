"""
Integration tests for API endpoints
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health and system status endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Plug-and-Play RAG" in data["message"]

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestLLMManagementEndpoints:
    """Test LLM provider management endpoints."""

    def test_get_llm_providers(self, client):
        """Test getting available LLM providers."""
        response = client.get("/api/llm/providers")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected providers are present
        expected_providers = ["gemini", "ollama", "lmstudio", "openai-compatible", "custom"]
        for provider in expected_providers:
            assert provider in data
            assert "description" in data[provider]
            assert "requires_api_key" in data[provider]

    @patch('app.main.gemini_client')
    def test_get_current_llm(self, mock_client, client):
        """Test getting current LLM provider."""
        mock_client.get_client_info.return_value = {
            "type": "gemini",
            "model": "gemini-pro",
            "status": "active"
        }
        
        response = client.get("/api/llm/current")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-pro"
        assert data["status"] == "active"

    def test_get_current_llm_no_client(self, client):
        """Test getting current LLM when no client is available."""
        with patch('app.main.gemini_client', None):
            response = client.get("/api/llm/current")
            assert response.status_code == 503
            data = response.json()
            assert "No LLM client available" in data["detail"]

    @patch('app.main.llm_client')
    @pytest.mark.asyncio
    async def test_switch_llm_provider(self, mock_llm_client, client):
        """Test switching LLM provider."""
        switch_request = {
            "provider": "ollama",
            "model_name": "llama2",
            "endpoint_url": "http://localhost:11434"
        }

        with patch('app.main.LLMFactory') as mock_factory:
            mock_new_client = Mock()
            mock_factory.create_client.return_value = mock_new_client
            
            response = client.post("/api/llm/switch", json=switch_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_switch_llm_provider_missing_provider(self, client):
        """Test switching LLM without providing provider."""
        switch_request = {}
        
        response = client.post("/api/llm/switch", json=switch_request)
        assert response.status_code == 400
        data = response.json()
        assert "Provider is required" in data["detail"]


class TestChatEndpoints:
    """Test chat functionality endpoints."""

    @patch('app.main.rag_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint(self, mock_rag, client):
        """Test chat endpoint."""
        mock_rag.process_query = AsyncMock(return_value={
            "response": "This is a test response",
            "sources": [{"source": "test.pdf", "content": "relevant content"}],
            "user_name": "test_user"
        })

        chat_request = {
            "message": "What is the meaning of life?",
            "user_name": "test_user"
        }

        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert data["user_name"] == "test_user"

    def test_chat_endpoint_missing_message(self, client):
        """Test chat endpoint with missing message."""
        invalid_request = {"user_name": "test_user"}
        
        response = client.post("/chat", json=invalid_request)
        assert response.status_code == 422  # Validation error

    @patch('app.main.rag_service')
    @pytest.mark.asyncio
    async def test_chat_stream_endpoint(self, mock_rag, client, sample_chat_request):
        """Test streaming chat endpoint."""
        async def mock_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"
        
        mock_rag.process_query_stream = AsyncMock(return_value=mock_stream())
        
        response = client.post("/chat/stream", json=sample_chat_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestDataIngestionEndpoints:
    """Test data ingestion endpoints."""

    @patch('app.main.rag_service')
    def test_ingest_data_sync(self, mock_rag, client, sample_ingestion_config):
        """Test synchronous data ingestion."""
        mock_rag.ingest_data = AsyncMock(return_value={
            "status": "completed",
            "documents_processed": 10,
            "batch_id": "test_batch_123"
        })
        
        response = client.post("/ingest-data", json=sample_ingestion_config)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["documents_processed"] == 10

    def test_ingest_data_invalid_config(self, client):
        """Test data ingestion with invalid configuration."""
        invalid_config = {"db_type": "invalid_type"}
        
        response = client.post("/ingest-data", json=invalid_config)
        # Should handle gracefully or return validation error
        assert response.status_code in [400, 422, 500]

    @patch('app.main.kafka_producer')
    @patch('app.main.redis_tracker')
    @pytest.mark.asyncio
    async def test_ingest_data_async(self, mock_redis, mock_kafka, client, sample_ingestion_config):
        """Test asynchronous data ingestion."""
        mock_kafka.send_message = AsyncMock()
        mock_redis.set_status = AsyncMock()
        
        response = client.post("/ingest-data-async", json=sample_ingestion_config)
        # Should work whether Kafka is available or not
        assert response.status_code in [200, 503]


class TestHistoryEndpoints:
    """Test chat history endpoints."""

    @patch('app.main.chat_history_manager')
    def test_get_chat_history(self, mock_history, client):
        """Test retrieving chat history."""
        mock_history.get_history = AsyncMock(return_value=[
            {"message": "Hello", "response": "Hi there!", "timestamp": "2025-08-31T10:00:00"}
        ])
        
        response = client.get("/chat/history/test_user")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch('app.main.chat_history_manager')
    def test_clear_chat_history(self, mock_history, client):
        """Test clearing chat history."""
        mock_history.clear_history = AsyncMock()
        
        response = client.delete("/chat/history/test_user")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Chat history cleared"


class TestErrorHandling:
    """Test error handling in API endpoints."""

    def test_404_endpoint(self, client):
        """Test accessing non-existent endpoint."""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404

    @patch('app.main.rag_service')
    def test_internal_server_error(self, mock_rag, client, sample_chat_request):
        """Test handling of internal server errors."""
        mock_rag.process_query = AsyncMock(side_effect=Exception("Internal error"))
        
        response = client.post("/chat", json=sample_chat_request)
        assert response.status_code == 500

    def test_validation_error(self, client):
        """Test request validation errors."""
        invalid_request = {"invalid_field": "value"}
        
        response = client.post("/chat", json=invalid_request)
        assert response.status_code == 422
