"""
Tests for CSV data ingestion functionality
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from app.database.csv_connector import CSVConnector
from app.models import CSVConfig, CSVColumnConfig, CSVColumnType


class TestCSVConnector:
    """Test CSV connector functionality."""

    @pytest.fixture
    def sample_csv_content(self):
        """Create sample CSV content."""
        return """title,content,category,score
"Article 1","Content of article 1","Tech",8.5
"Article 2","Content of article 2","Science",9.0
"Article 3","Content of article 3","Tech",7.8"""

    @pytest.fixture
    def csv_config(self, sample_csv_content):
        """Create CSV configuration for testing."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = f.name
        
        config = CSVConfig(
            file_path=temp_path,
            columns=[
                CSVColumnConfig(name="title", type=CSVColumnType.TEXT, required=True),
                CSVColumnConfig(name="content", type=CSVColumnType.TEXT, required=True),
                CSVColumnConfig(name="category", type=CSVColumnType.TEXT),
                CSVColumnConfig(name="score", type=CSVColumnType.FLOAT)
            ],
            text_columns=["title", "content"],
            metadata_columns=["category", "score"]
        )
        
        yield config
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_csv_connector_initialization(self, csv_config):
        """Test CSV connector initialization."""
        connector = CSVConnector(csv_config)
        assert connector.csv_config == csv_config
        assert connector.df is None

    @pytest.mark.asyncio
    async def test_csv_connector_connect(self, csv_config):
        """Test CSV connector connection and data loading."""
        connector = CSVConnector(csv_config)
        await connector.connect()
        
        assert connector.df is not None
        assert len(connector.df) == 3
        assert list(connector.df.columns) == ["title", "content", "category", "score"]

    @pytest.mark.asyncio
    async def test_csv_fetch_data(self, csv_config):
        """Test fetching data from CSV."""
        connector = CSVConnector(csv_config)
        await connector.connect()
        
        # Fetch all data
        records = await connector.fetch_data("dummy_table")
        assert len(records) == 3
        assert "title" in records[0]
        assert "content" in records[0]
        
        # Fetch with limit
        limited_records = await connector.fetch_data("dummy_table", limit=2)
        assert len(limited_records) == 2
        
        # Fetch with offset
        offset_records = await connector.fetch_data("dummy_table", offset=1, limit=1)
        assert len(offset_records) == 1
        assert offset_records[0]["title"] == "Article 2"

    @pytest.mark.asyncio
    async def test_csv_fetch_in_chunks(self, csv_config):
        """Test fetching data in chunks."""
        connector = CSVConnector(csv_config)
        await connector.connect()
        
        chunks = []
        async for chunk in connector.fetch_in_chunks(chunk_size=2):
            chunks.append(chunk)
        
        assert len(chunks) == 2  # 3 rows, chunk size 2 = 2 chunks
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1

    def test_csv_get_text_content(self, csv_config):
        """Test extracting text content from record."""
        connector = CSVConnector(csv_config)
        
        record = {
            "title": "Test Title",
            "content": "Test Content", 
            "category": "Tech",
            "score": 8.5
        }
        
        text_content = connector.get_text_content(record)
        assert text_content == "Test Title Test Content"

    def test_csv_get_metadata(self, csv_config):
        """Test extracting metadata from record."""
        connector = CSVConnector(csv_config)
        
        record = {
            "title": "Test Title",
            "content": "Test Content",
            "category": "Tech", 
            "score": 8.5
        }
        
        metadata = connector.get_metadata(record)
        assert metadata["source"] == "csv"
        assert metadata["category"] == "Tech"
        assert metadata["score"] == 8.5
        assert "file_path" in metadata

    @pytest.mark.asyncio
    async def test_csv_invalid_file(self):
        """Test CSV connector with invalid file path."""
        config = CSVConfig(
            file_path="non_existent_file.csv",
            columns=[CSVColumnConfig(name="col1", type=CSVColumnType.TEXT)],
            text_columns=["col1"]
        )
        
        with pytest.raises(FileNotFoundError):
            CSVConnector(config)

    @pytest.mark.asyncio
    async def test_csv_column_validation(self, sample_csv_content):
        """Test CSV configuration validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = f.name
        
        try:
            # Test invalid text column
            config = CSVConfig(
                file_path=temp_path,
                columns=[CSVColumnConfig(name="title", type=CSVColumnType.TEXT)],
                text_columns=["invalid_column"]  # Column not in definitions
            )
            
            with pytest.raises(ValueError, match="Text column 'invalid_column' not found"):
                CSVConnector(config)
                
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_csv_data_type_processing(self):
        """Test CSV data type processing."""
        csv_content = """name,age,active,data,created_date
"John",25,true,"{""key"": ""value""}","2024-01-01"
"Jane",30,false,"{""foo"": ""bar""}","2024-02-01"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            config = CSVConfig(
                file_path=temp_path,
                columns=[
                    CSVColumnConfig(name="name", type=CSVColumnType.TEXT),
                    CSVColumnConfig(name="age", type=CSVColumnType.INTEGER),
                    CSVColumnConfig(name="active", type=CSVColumnType.BOOLEAN),
                    CSVColumnConfig(name="data", type=CSVColumnType.JSON),
                    CSVColumnConfig(name="created_date", type=CSVColumnType.DATETIME)
                ],
                text_columns=["name"]
            )
            
            connector = CSVConnector(config)
            await connector.connect()
            
            records = await connector.fetch_data("dummy")
            
            # Check data types
            assert isinstance(records[0]["age"], int)
            assert isinstance(records[0]["active"], bool)
            assert isinstance(records[0]["data"], dict)
            assert records[0]["active"] is True
            assert records[1]["active"] is False
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCSVAPIEndpoints:
    """Test CSV-related API endpoints."""

    @pytest.fixture
    def sample_csv_config(self):
        """Sample CSV configuration for API testing."""
        return {
            "file_path": "/tmp/test.csv",
            "delimiter": ",",
            "has_header": True,
            "encoding": "utf-8",
            "columns": [
                {"name": "title", "type": "text", "required": True},
                {"name": "content", "type": "text", "required": True}
            ],
            "text_columns": ["title", "content"],
            "chunk_size": 100
        }

    def test_ingest_csv_endpoint(self, client, sample_csv_config):
        """Test CSV ingestion endpoint."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('app.main.rag_service') as mock_rag:
                mock_rag.ingest_data_background = AsyncMock()
                
                response = client.post("/ingest-csv", json=sample_csv_config)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "processing"
                assert "CSV data ingestion started" in data["message"]
                assert data["file_path"] == sample_csv_config["file_path"]

    def test_ingest_csv_file_not_found(self, client, sample_csv_config):
        """Test CSV ingestion with non-existent file."""
        with patch('pathlib.Path.exists', return_value=False):
            response = client.post("/ingest-csv", json=sample_csv_config)
            
            assert response.status_code == 404
            data = response.json()
            assert "CSV file not found" in data["detail"]

    @patch('app.database.csv_connector.CSVConnector')
    def test_validate_csv_endpoint(self, mock_connector_class, client, sample_csv_config):
        """Test CSV validation endpoint."""
        # Mock connector
        mock_connector = Mock()
        mock_connector.get_schema_info.return_value = {
            "total_rows": 10,
            "total_columns": 2,
            "columns": {"title": {}, "content": {}}
        }
        mock_connector.connect = AsyncMock()
        mock_connector.disconnect = AsyncMock()
        mock_connector_class.return_value = mock_connector
        
        response = client.post("/validate-csv", json=sample_csv_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert "schema_info" in data

    @patch('pandas.read_csv')
    def test_csv_sample_endpoint(self, mock_read_csv, client):
        """Test CSV sample endpoint."""
        # Mock pandas dataframe
        mock_df = pd.DataFrame({
            "title": ["Article 1", "Article 2"],
            "content": ["Content 1", "Content 2"]
        })
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):
            response = client.get("/csv-sample/test.csv?rows=2")
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_path"] == "test.csv"
            assert len(data["columns"]) == 2
            assert len(data["sample_rows"]) == 2

    def test_csv_sample_file_not_found(self, client):
        """Test CSV sample endpoint with non-existent file."""
        response = client.get("/csv-sample/non_existent.csv")
        
        assert response.status_code == 404
        data = response.json()
        assert "CSV file not found" in data["detail"]


class TestCSVRAGIntegration:
    """Test CSV integration with RAG service."""

    @pytest.fixture
    def mock_csv_connector(self):
        """Mock CSV connector for RAG testing."""
        connector = Mock(spec=CSVConnector)
        
        # Mock chunk data
        async def mock_fetch_in_chunks():
            yield [
                {"title": "AI Basics", "content": "Introduction to AI"},
                {"title": "ML Guide", "content": "Machine learning guide"}
            ]
        
        connector.fetch_in_chunks.return_value = mock_fetch_in_chunks()
        connector.get_text_content.side_effect = lambda record: f"{record['title']} {record['content']}"
        connector.get_metadata.side_effect = lambda record: {"source": "csv", "title": record["title"]}
        connector.disconnect = AsyncMock()
        
        return connector

    @pytest.mark.asyncio
    async def test_rag_csv_ingestion(self, mock_csv_connector):
        """Test RAG service CSV data ingestion."""
        from app.chat.rag_service import RAGService
        from app.models import DataSourceConfig, DatabaseType
        
        # Mock dependencies
        mock_embedding_manager = Mock()
        mock_embedding_manager.add_documents = AsyncMock()
        mock_gemini_client = Mock()
        mock_history_manager = Mock()
        
        rag_service = RAGService(
            embedding_manager=mock_embedding_manager,
            gemini_client=mock_gemini_client,
            history_manager=mock_history_manager
        )
        
        # Test CSV ingestion
        config = DataSourceConfig(
            db_type=DatabaseType.CSV,
            connection_params={"file_path": "test.csv"},
            table_or_collection="dummy",
            columns_or_fields=["title", "content"],
            text_fields=["title", "content"]
        )
        
        with patch('app.chat.rag_service.DatabaseFactory') as mock_factory:
            mock_factory.return_value.create_connector = AsyncMock(return_value=mock_csv_connector)
            
            await rag_service._ingest_csv_data(mock_csv_connector, config)
            
            # Verify documents were added
            mock_embedding_manager.add_documents.assert_called_once()
            call_args = mock_embedding_manager.add_documents.call_args
            documents, metadatas = call_args[0]
            
            assert len(documents) == 2
            assert "AI Basics Introduction to AI" in documents
            assert "ML Guide Machine learning guide" in documents
            assert len(metadatas) == 2
            assert metadatas[0]["source"] == "csv"

    @pytest.mark.asyncio
    async def test_csv_data_with_empty_text(self, mock_csv_connector):
        """Test CSV data processing with empty text content."""
        from app.chat.rag_service import RAGService
        from app.models import DataSourceConfig, DatabaseType
        
        # Mock connector with empty text content
        async def mock_fetch_in_chunks_with_empty():
            yield [
                {"title": "Valid Article", "content": "Good content"},
                {"title": "", "content": ""},  # Empty text
                {"title": "Another Article", "content": "More content"}
            ]
        
        mock_csv_connector.fetch_in_chunks.return_value = mock_fetch_in_chunks_with_empty()
        mock_csv_connector.get_text_content.side_effect = lambda record: f"{record['title']} {record['content']}".strip()
        
        mock_embedding_manager = Mock()
        mock_embedding_manager.add_documents = AsyncMock()
        mock_gemini_client = Mock()
        mock_history_manager = Mock()
        
        rag_service = RAGService(
            embedding_manager=mock_embedding_manager,
            gemini_client=mock_gemini_client,
            history_manager=mock_history_manager
        )
        
        config = DataSourceConfig(
            db_type=DatabaseType.CSV,
            connection_params={"file_path": "test.csv"},
            table_or_collection="dummy",
            columns_or_fields=["title", "content"],
            text_fields=["title", "content"]
        )
        
        await rag_service._ingest_csv_data(mock_csv_connector, config)
        
        # Should only process records with non-empty text
        mock_embedding_manager.add_documents.assert_called_once()
        call_args = mock_embedding_manager.add_documents.call_args
        documents, metadatas = call_args[0]
        
        assert len(documents) == 2  # Only non-empty records
        assert "Valid Article Good content" in documents
        assert "Another Article More content" in documents
