"""
Unit tests for core services
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from app.embeddings.manager import EmbeddingManager
from app.chat.rag_service import RAGService
from app.chat.history_manager import ChatHistoryManager


class TestEmbeddingManager:
    """Test embedding manager functionality."""

    @patch('app.embeddings.manager.SentenceTransformer')
    @patch('app.embeddings.manager.chromadb.PersistentClient')
    def test_embedding_manager_init(self, mock_chroma, mock_transformer):
        """Test EmbeddingManager initialization."""
        mock_transformer.return_value = Mock()
        mock_chroma.return_value = Mock()
        
        manager = EmbeddingManager()
        
        assert manager is not None
        mock_transformer.assert_called_once()
        mock_chroma.assert_called_once()

    @patch('app.embeddings.manager.SentenceTransformer')
    @patch('app.embeddings.manager.chromadb.PersistentClient') 
    @pytest.mark.asyncio
    async def test_create_embeddings(self, mock_chroma, mock_transformer):
        """Test creating embeddings."""
        # Mock transformer
        mock_transformer_instance = Mock()
        mock_transformer_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_transformer_instance
        
        # Mock chroma client
        mock_chroma_instance = Mock()
        mock_chroma.return_value = mock_chroma_instance
        
        manager = EmbeddingManager()
        texts = ["This is a test document"]
        
        with patch.object(manager, 'model', mock_transformer_instance):
            embeddings = await manager.create_embeddings(texts)
        
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 3
        mock_transformer_instance.encode.assert_called_once_with(texts)

    @patch('app.embeddings.manager.SentenceTransformer')
    @patch('app.embeddings.manager.chromadb.PersistentClient')
    @pytest.mark.asyncio
    async def test_search_similar(self, mock_chroma, mock_transformer):
        """Test searching for similar documents."""
        # Mock transformer
        mock_transformer_instance = Mock()
        mock_transformer_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_transformer_instance
        
        # Mock chroma collection
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'documents': [['Similar document']],
            'metadatas': [[{'source': 'test'}]],
            'distances': [[0.1]]
        }
        
        # Mock chroma client
        mock_chroma_instance = Mock()
        mock_chroma_instance.get_collection.return_value = mock_collection
        mock_chroma.return_value = mock_chroma_instance
        
        manager = EmbeddingManager()
        
        with patch.object(manager, 'model', mock_transformer_instance):
            with patch.object(manager, 'collection', mock_collection):
                results = await manager.search_similar("test query", k=1)
        
        assert len(results) == 1
        assert results[0]['document'] == 'Similar document'

    @patch('app.embeddings.manager.SentenceTransformer')
    @patch('app.embeddings.manager.chromadb.PersistentClient')
    @pytest.mark.asyncio
    async def test_add_documents(self, mock_chroma, mock_transformer):
        """Test adding documents to the collection."""
        # Mock transformer
        mock_transformer_instance = Mock()
        mock_transformer_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_transformer_instance
        
        # Mock chroma collection
        mock_collection = Mock()
        mock_chroma_instance = Mock()
        mock_chroma_instance.get_collection.return_value = mock_collection
        mock_chroma.return_value = mock_chroma_instance
        
        manager = EmbeddingManager()
        
        documents = ["Test document"]
        metadatas = [{"source": "test"}]
        
        with patch.object(manager, 'model', mock_transformer_instance):
            with patch.object(manager, 'collection', mock_collection):
                await manager.add_documents(documents, metadatas)
        
        mock_collection.add.assert_called_once()


class TestChatHistoryManager:
    """Test chat history manager functionality."""

    @patch('os.makedirs')
    def test_chat_history_init(self, mock_makedirs):
        """Test ChatHistoryManager initialization."""
        history_manager = ChatHistoryManager(history_dir="./test_history")
        
        assert history_manager.history_dir == "./test_history"
        mock_makedirs.assert_called_once()

    @patch('builtins.open', new_callable=Mock)
    @patch('json.load')
    @patch('json.dump')
    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_add_message(self, mock_exists, mock_dump, mock_load, mock_open):
        """Test adding a message to chat history."""
        mock_exists.return_value = False  # File doesn't exist
        mock_load.return_value = []
        
        history_manager = ChatHistoryManager()
        
        await history_manager.add_message(
            user_name="test_user",
            role="user", 
            content="Hello world"
        )
        
        mock_open.assert_called()
        mock_dump.assert_called()

    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_get_empty_history(self, mock_exists):
        """Test getting empty history for new user."""
        mock_exists.return_value = False
        
        history_manager = ChatHistoryManager()
        history = await history_manager.get_history("new_user")
        
        assert history == []

    @patch('builtins.open', new_callable=Mock)
    @patch('json.load')
    @patch('json.dump')
    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_clear_history(self, mock_exists, mock_dump, mock_load, mock_open):
        """Test clearing chat history."""
        mock_exists.return_value = True
        mock_load.return_value = [{"role": "user", "content": "test"}]
        
        history_manager = ChatHistoryManager()
        
        # Add a message first
        await history_manager.add_message("test_user", "user", "Hello")
        
        # Clear history
        await history_manager.clear_history("test_user")
        
        # Verify file operations
        mock_open.assert_called()

    @patch('builtins.open', new_callable=Mock)
    @patch('json.load')
    @patch('json.dump')
    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_history_limit(self, mock_exists, mock_dump, mock_load, mock_open):
        """Test history limiting functionality."""
        # Mock existing large history
        large_history = [{"role": "user", "content": f"message {i}"} for i in range(100)]
        mock_exists.return_value = True
        mock_load.return_value = large_history
        
        history_manager = ChatHistoryManager(history_dir="./test")
        
        history = await history_manager.get_history("test_user", limit=10)
        
        # Should return limited history
        assert len(history) <= 10

    @patch('builtins.open', new_callable=Mock)
    @patch('json.load')  
    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_get_context(self, mock_exists, mock_load, mock_open):
        """Test getting context from chat history."""
        mock_history = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI stands for Artificial Intelligence"}
        ]
        mock_exists.return_value = True
        mock_load.return_value = mock_history
        
        history_manager = ChatHistoryManager()
        
        context = await history_manager.get_context("test_user")
        
        assert len(context) > 0
        assert "AI" in context


class TestRAGService:
    """Test RAG service functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_embedding_manager = Mock()
        self.mock_gemini_client = Mock()  # Changed from llm_client to gemini_client
        self.mock_chat_history = Mock()

        self.rag_service = RAGService(
            embedding_manager=self.mock_embedding_manager,
            gemini_client=self.mock_gemini_client,  # Updated parameter name
            history_manager=self.mock_chat_history
        )

    @pytest.mark.asyncio
    async def test_process_query_basic(self):
        """Test basic query processing."""
        # Mock search results
        self.mock_embedding_manager.search_similar.return_value = [
            {"document": "Test document", "metadata": {"source": "test"}}
        ]
        
        # Mock LLM response
        self.mock_gemini_client.generate_response = AsyncMock(
            return_value="This is a test response"
        )
        
        # Mock history
        self.mock_chat_history.get_context.return_value = "Previous context"
        self.mock_chat_history.add_message = AsyncMock()
        
        result = await self.rag_service.process_query(
            query="What is a test?",
            user_name="test_user"
        )
        
        assert "response" in result
        assert result["response"] == "This is a test response"
        
        # Verify methods were called
        self.mock_embedding_manager.search_similar.assert_called_once()
        self.mock_gemini_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_no_sources(self):
        """Test query processing when no relevant sources found."""
        # Mock empty search results
        self.mock_embedding_manager.search_similar.return_value = []
        
        # Mock LLM response
        self.mock_gemini_client.generate_response = AsyncMock(
            return_value="No relevant information found"
        )
        
        # Mock history
        self.mock_chat_history.get_context.return_value = ""
        self.mock_chat_history.add_message = AsyncMock()
        
        result = await self.rag_service.process_query(
            query="Unknown topic",
            user_name="test_user"
        )
        
        assert "response" in result
        self.mock_embedding_manager.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_with_context(self):
        """Test query processing with chat context."""
        # Mock search results with context
        self.mock_embedding_manager.search_similar.return_value = [
            {"document": "Context document", "metadata": {"source": "context"}}
        ]
        
        # Mock LLM response
        self.mock_gemini_client.generate_response = AsyncMock(
            return_value="Response with context"
        )
        
        # Mock chat history context
        self.mock_chat_history.get_context.return_value = "Previous conversation context"
        self.mock_chat_history.add_message = AsyncMock()
        
        result = await self.rag_service.process_query(
            query="Follow up question",
            user_name="test_user"
        )
        
        assert "response" in result
        self.mock_chat_history.get_context.assert_called_once()

    @pytest.mark.asyncio  
    async def test_ingest_data_demo(self):
        """Test data ingestion from demo data."""
        # Mock embedding manager
        self.mock_embedding_manager.add_documents = AsyncMock()
        
        # Mock demo data
        demo_config = Mock()
        demo_config.db_type = "demo"
        demo_config.table_or_collection = "test_articles"
        demo_config.text_fields = ["title", "content"]
        demo_config.connection_params = {}
        
        # Test the background ingestion
        with patch('app.chat.rag_service.DatabaseFactory') as mock_factory:
            mock_connector = Mock()
            mock_connector.fetch_data = AsyncMock(return_value=[
                {"title": "Test Article", "content": "Test content"}
            ])
            mock_factory.return_value.create_connector = AsyncMock(return_value=mock_connector)
            
            await self.rag_service.ingest_data_background(demo_config)
            
            # Verify data was processed
            mock_connector.fetch_data.assert_called_once()
            self.mock_embedding_manager.add_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_stream(self):
        """Test streaming query processing."""
        # Mock search results
        self.mock_embedding_manager.search_similar.return_value = [
            {"document": "Streaming test", "metadata": {"source": "stream"}}
        ]
        
        # Mock streaming LLM response
        async def mock_stream():
            yield "Chunk 1"
            yield "Chunk 2"
            yield "Chunk 3"
        
        self.mock_gemini_client.generate_response_stream = AsyncMock(
            return_value=mock_stream()
        )
        
        # Mock history
        self.mock_chat_history.get_context.return_value = ""
        self.mock_chat_history.add_message = AsyncMock()
        
        # Test streaming
        stream = self.rag_service.process_query_stream(
            query="Stream test",
            user_name="test_user"
        )
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk.content)
        
        assert len(chunks) > 0
