"""
Configuration-driven application initialization
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.config.manager import get_config, PlugAndPlayConfig
from app.database.factory import DatabaseFactory
from app.database.csv_connector import CSVConnector
from app.models import DataSourceConfig, DatabaseType, CSVConfig
from app.chat.rag_service import RAGService
from app.embeddings.manager import EmbeddingManager
from app.ai.gemini_client import GeminiClient
from app.ai.multi_llm_client import MultiLLMClient
from app.chat.history_manager import ChatHistoryManager


logger = logging.getLogger(__name__)


class ConfigDrivenApp:
    """Configuration-driven application initialization and management."""
    
    def __init__(self, config_path: str = None):
        """Initialize with optional custom config path."""
        self.config: PlugAndPlayConfig = None
        self.rag_service: RAGService = None
        self.embedding_manager: EmbeddingManager = None
        self.llm_client = None
        self.history_manager: ChatHistoryManager = None
        
        if config_path:
            from app.config.manager import ConfigManager
            manager = ConfigManager(config_path)
            self.config = manager.load_config()
        else:
            self.config = get_config()
    
    async def initialize_services(self):
        """Initialize all services based on configuration."""
        logger.info("Initializing services from configuration...")
        
        # 1. Initialize embedding manager
        await self._initialize_embedding_manager()
        
        # 2. Initialize LLM client
        await self._initialize_llm_client()
        
        # 3. Initialize chat history manager
        await self._initialize_history_manager()
        
        # 4. Initialize RAG service
        await self._initialize_rag_service()
        
        # 5. Auto-ingest data if configured
        if self.config.auto_ingest_on_startup:
            await self._auto_ingest_data()
        
        logger.info("All services initialized successfully")
    
    async def _initialize_embedding_manager(self):
        """Initialize embedding manager from config."""
        config = self.config.embedding
        
        logger.info(f"Initializing embedding manager with model: {config.model_name}")
        self.embedding_manager = EmbeddingManager(
            model_name=config.model_name,
            collection_name=self.config.vector_db.collection_name,
            persist_directory=self.config.vector_db.persist_directory
        )
        await self.embedding_manager.initialize()
    
    async def _initialize_llm_client(self):
        """Initialize LLM client based on provider configuration."""
        llm_config = self.config.llm
        
        logger.info(f"Initializing LLM client: {llm_config.provider}")
        
        if llm_config.provider == "gemini":
            self.llm_client = GeminiClient(
                api_key=llm_config.api_key,
                model_name=llm_config.model_name
            )
        else:
            # Use multi-LLM client for other providers
            self.llm_client = MultiLLMClient(
                provider=llm_config.provider,
                api_key=llm_config.api_key,
                api_url=llm_config.api_url,
                model_name=llm_config.model_name,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                custom_headers=llm_config.custom_headers,
                request_format=llm_config.request_format,
                response_format=llm_config.response_format
            )
    
    async def _initialize_history_manager(self):
        """Initialize chat history manager."""
        if self.config.enable_chat_history:
            logger.info("Initializing chat history manager")
            self.history_manager = ChatHistoryManager()
        else:
            logger.info("Chat history disabled in configuration")
            self.history_manager = None
    
    async def _initialize_rag_service(self):
        """Initialize RAG service with all components."""
        logger.info("Initializing RAG service")
        self.rag_service = RAGService(
            embedding_manager=self.embedding_manager,
            gemini_client=self.llm_client,  # Works with both Gemini and MultiLLM clients
            history_manager=self.history_manager
        )
    
    async def _auto_ingest_data(self):
        """Auto-ingest data sources configured for startup."""
        logger.info("Starting auto-ingestion of configured data sources...")
        
        ingestion_tasks = []
        
        # Process CSV sources
        if self.config.csv_sources:
            for csv_source in self.config.csv_sources:
                task = self._ingest_csv_source(csv_source)
                ingestion_tasks.append(task)
        
        # Process database sources
        if self.config.database_sources:
            for db_source in self.config.database_sources:
                task = self._ingest_database_source(db_source)
                ingestion_tasks.append(task)
        
        # Run all ingestion tasks
        if ingestion_tasks:
            results = await asyncio.gather(*ingestion_tasks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Ingestion task {i} failed: {result}")
                else:
                    logger.info(f"Ingestion task {i} completed successfully")
        
        logger.info("Auto-ingestion completed")
    
    async def _ingest_csv_source(self, csv_config):
        """Ingest a single CSV data source."""
        try:
            logger.info(f"Ingesting CSV source: {csv_config.name}")
            
            # Resolve file path relative to data directory
            data_dir = Path("/app/data")  # Docker container path
            file_path = data_dir / csv_config.file_path
            
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            # Create CSV configuration
            csv_config_obj = CSVConfig(
                file_path=str(file_path),
                delimiter=csv_config.delimiter,
                has_header=csv_config.has_header,
                encoding=csv_config.encoding,
                columns=csv_config.columns,
                text_columns=csv_config.text_columns,
                metadata_columns=csv_config.metadata_columns,
                chunk_size=csv_config.chunk_size,
                skip_rows=csv_config.skip_rows,
                max_rows=csv_config.max_rows
            )
            
            # Create data source config
            data_source_config = DataSourceConfig(
                db_type=DatabaseType.CSV,
                connection_params=csv_config_obj.model_dump(),
                table_or_collection="csv_data",
                columns_or_fields=csv_config.text_columns,
                text_fields=csv_config.text_columns
            )
            
            # Ingest the data
            await self.rag_service.ingest_data_background(data_source_config)
            logger.info(f"Successfully ingested CSV source: {csv_config.name}")
            
        except Exception as e:
            logger.error(f"Failed to ingest CSV source {csv_config.name}: {e}")
            raise
    
    async def _ingest_database_source(self, db_source):
        """Ingest a single database data source."""
        try:
            logger.info(f"Ingesting database source: {db_source.name}")
            
            # Get database configuration
            db_config = self.config.databases.get(db_source.database_config)
            if not db_config:
                raise ValueError(f"Database configuration not found: {db_source.database_config}")
            
            # Create connection parameters
            connection_params = {
                "host": db_config.host,
                "port": db_config.port,
                "database": db_config.database,
                "username": db_config.username,
                "password": db_config.password
            }
            
            if db_config.connection_params:
                connection_params.update(db_config.connection_params)
            
            # Create data source config
            data_source_config = DataSourceConfig(
                db_type=db_config.type,
                connection_params=connection_params,
                table_or_collection=db_source.table_or_collection,
                columns_or_fields=db_source.columns_or_fields,
                text_fields=db_source.text_fields
            )
            
            # Ingest the data
            await self.rag_service.ingest_data_background(data_source_config)
            logger.info(f"Successfully ingested database source: {db_source.name}")
            
        except Exception as e:
            logger.error(f"Failed to ingest database source {db_source.name}: {e}")
            raise
    
    def get_rag_service(self) -> RAGService:
        """Get the initialized RAG service."""
        if not self.rag_service:
            raise RuntimeError("RAG service not initialized. Call initialize_services() first.")
        return self.rag_service
    
    def get_config(self) -> PlugAndPlayConfig:
        """Get the current configuration."""
        return self.config
    
    async def shutdown(self):
        """Shutdown all services gracefully."""
        logger.info("Shutting down services...")
        
        if self.embedding_manager:
            await self.embedding_manager.cleanup()
        
        if self.history_manager:
            # Add cleanup if needed
            pass
        
        logger.info("All services shut down successfully")


# Global app instance
app_instance: ConfigDrivenApp = None


def get_app() -> ConfigDrivenApp:
    """Get the global app instance."""
    global app_instance
    if app_instance is None:
        app_instance = ConfigDrivenApp()
    return app_instance


async def initialize_app(config_path: str = None) -> ConfigDrivenApp:
    """Initialize the application with configuration."""
    global app_instance
    app_instance = ConfigDrivenApp(config_path)
    await app_instance.initialize_services()
    return app_instance
