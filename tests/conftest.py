"""
Test configuration and fixtures for Plug-and-Play RAG
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.ai.llm_factory import LLMFactory
from app.embeddings.manager import EmbeddingManager
from app.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock_client = Mock()
    mock_client.generate_response = AsyncMock(return_value="Test response")
    mock_client.generate_response_stream = AsyncMock()
    mock_client.get_client_info = Mock(return_value={
        "type": "test",
        "model": "test-model",
        "provider": "test-provider"
    })
    return mock_client

@pytest.fixture
def mock_embedding_manager():
    """Mock embedding manager for testing."""
    mock_manager = Mock(spec=EmbeddingManager)
    mock_manager.create_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    mock_manager.search_similar = AsyncMock(return_value=[
        {"content": "Test document 1", "metadata": {"score": 0.95}},
        {"content": "Test document 2", "metadata": {"score": 0.85}}
    ])
    mock_manager.add_documents = AsyncMock()
    return mock_manager

@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return {
        "message": "What is machine learning?",
        "user_name": "test_user"
    }

@pytest.fixture
def sample_ingestion_config():
    """Sample data ingestion configuration."""
    return {
        "db_type": "demo",
        "table_or_collection": "test_articles",
        "text_fields": ["title", "content"]
    }

@pytest.fixture
def sample_llm_switch_request():
    """Sample LLM provider switch request."""
    return {
        "provider": "test_provider",
        "model_name": "test_model",
        "endpoint_url": "http://localhost:8080/chat"
    }

# Test data fixtures
@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "title": "Introduction to AI",
            "content": "Artificial Intelligence is a broad field of computer science focused on creating smart machines.",
            "metadata": {"category": "AI", "author": "John Doe"}
        },
        {
            "id": "doc2", 
            "title": "Machine Learning Basics",
            "content": "Machine learning is a subset of AI that focuses on algorithms that can learn from data.",
            "metadata": {"category": "ML", "author": "Jane Smith"}
        },
        {
            "id": "doc3",
            "title": "Deep Learning Networks",
            "content": "Deep learning uses neural networks with multiple layers to model complex patterns.",
            "metadata": {"category": "DL", "author": "Bob Johnson"}
        }
    ]

@pytest.fixture
def mock_database():
    """Mock database for testing."""
    mock_db = Mock()
    mock_db.connect = AsyncMock()
    mock_db.disconnect = AsyncMock()
    mock_db.fetch_data = AsyncMock(return_value=[
        {"id": 1, "title": "Test Article", "content": "Test content"}
    ])
    return mock_db

# Environment fixtures
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("DEBUG", "true")

# Cleanup fixtures
@pytest.fixture(scope="function")
def cleanup_test_data():
    """Clean up test data after each test."""
    # Setup code here if needed
    yield
    # Cleanup code here
    import shutil
    import os
    
    # Clean up test directories
    test_dirs = ["./test_history", "./test_chroma_db", "./test_embeddings"]
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                pass  # Ignore cleanup errors in tests
