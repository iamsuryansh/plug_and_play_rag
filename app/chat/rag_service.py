from typing import List, Dict, Any, AsyncIterator
import logging
from datetime import datetime

from ..models import ChatRequest, ChatResponse, DataSourceConfig, StreamChunk, DatabaseType
from ..database.factory import DatabaseFactory
from ..database.csv_connector import CSVConnector
from ..embeddings.manager import EmbeddingManager
from ..ai.gemini_client import GeminiClient
from ..chat.history_manager import ChatHistoryManager

logger = logging.getLogger(__name__)

class RAGService:
    """Main service orchestrating the RAG pipeline."""
    
    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        gemini_client: GeminiClient,
        history_manager: ChatHistoryManager
    ):
        self.embedding_manager = embedding_manager
        self.gemini_client = gemini_client
        self.history_manager = history_manager
    
    async def ingest_data_background(self, config: DataSourceConfig) -> None:
        """
        Background task to ingest data from database and create embeddings.
        
        Args:
            config: Data source configuration
        """
        try:
            logger.info(f"Starting data ingestion for {config.db_type} table/collection: {config.table_or_collection}")
            
            # Create database connector
            db_factory = DatabaseFactory()
            db_connector = await db_factory.create_connector(
                config.db_type,
                config.connection_params
            )
            
            # Handle CSV data ingestion differently
            if config.db_type == DatabaseType.CSV:
                await self._ingest_csv_data(db_connector, config)
            else:
                await self._ingest_database_data(db_connector, config)
            
            # Cleanup database connection
            await db_connector.disconnect()
            
        except Exception as e:
            logger.error(f"Error in background data ingestion: {e}")
            raise
    
    async def _ingest_csv_data(self, db_connector: CSVConnector, config: DataSourceConfig) -> None:
        """
        Ingest data from CSV file.
        
        Args:
            db_connector: CSV database connector
            config: Data source configuration
        """
        count = 0
        documents = []
        metadatas = []
        
        # Process CSV data in chunks for memory efficiency
        async for chunk in db_connector.fetch_in_chunks():
            for record in chunk:
                # Get text content for embedding
                text_content = db_connector.get_text_content(record)
                if text_content.strip():  # Only process non-empty text
                    documents.append(text_content)
                    metadatas.append(db_connector.get_metadata(record))
                    count += 1
                    
                    # Process in batches to avoid memory issues
                    if len(documents) >= 100:
                        await self.embedding_manager.add_documents(documents, metadatas)
                        documents = []
                        metadatas = []
                        logger.info(f"Processed {count} CSV records so far...")
        
        # Process remaining documents
        if documents:
            await self.embedding_manager.add_documents(documents, metadatas)
        
        logger.info(f"CSV data ingestion completed. Total records processed: {count}")
    
    async def _ingest_database_data(self, db_connector, config: DataSourceConfig) -> None:
        """
        Ingest data from traditional databases.
        
        Args:
            db_connector: Database connector
            config: Data source configuration
        """
        # Fetch data from database
        records = await db_connector.fetch_data(
            config.table_or_collection,
            config.columns_or_fields
        )
        
        documents = []
        metadatas = []
        count = 0
        
        for record in records:
            # Combine text fields
            text_parts = []
            for field in config.text_fields:
                if field in record and record[field]:
                    text_parts.append(str(record[field]))
            
            text_content = " ".join(text_parts)
            if text_content.strip():
                documents.append(text_content)
                metadatas.append({
                    "source": config.db_type,
                    "table": config.table_or_collection,
                    **{k: v for k, v in record.items() if k not in config.text_fields}
                })
                count += 1
                
                # Process in batches
                if len(documents) >= 100:
                    await self.embedding_manager.add_documents(documents, metadatas)
                    documents = []
                    metadatas = []
                    logger.info(f"Processed {count} database records so far...")
        
        # Process remaining documents
        if documents:
            await self.embedding_manager.add_documents(documents, metadatas)
            
        logger.info(f"Database data ingestion completed. Total records processed: {count}")
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request using RAG approach.
        
        Args:
            request: Chat request from user
            
        Returns:
            Chat response with AI-generated answer
        """
        try:
            # Get chat history if requested
            chat_history = []
            if request.include_history:
                chat_history = await self.history_manager.get_history(request.user_name)
            
            # Search for relevant context
            context_documents = await self.embedding_manager.search_similar(
                request.message,
                n_results=request.max_results
            )
            
            # Generate AI response
            ai_response = await self.gemini_client.generate_response(
                request.message,
                context_documents,
                chat_history
            )
            
            # Save user message to history
            await self.history_manager.add_message(
                request.user_name,
                "user",
                request.message
            )
            
            # Save AI response to history
            await self.history_manager.add_message(
                request.user_name,
                "assistant",
                ai_response,
                {"sources": [doc.get("metadata", {}) for doc in context_documents]}
            )
            
            # Format sources for response
            sources = []
            for doc in context_documents:
                source = {
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "relevance_score": 1 - doc.get("distance", 0) if doc.get("distance") is not None else None
                }
                sources.append(source)
            
            return ChatResponse(
                user_name=request.user_name,
                response=ai_response,
                sources=sources,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            raise
    
    async def process_chat_request_stream(
        self,
        request: ChatRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a chat request with streaming response.
        
        Args:
            request: Chat request from user
            
        Yields:
            Stream chunks with response content
        """
        try:
            # Get chat history if requested
            chat_history = []
            if request.include_history:
                chat_history = await self.history_manager.get_history(request.user_name)
            
            # Search for relevant context
            context_documents = await self.embedding_manager.search_similar(
                request.message,
                n_results=request.max_results
            )
            
            # Yield sources first
            sources = []
            for doc in context_documents:
                source = {
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "relevance_score": 1 - doc.get("distance", 0) if doc.get("distance") is not None else None
                }
                sources.append(source)
            
            yield {
                "type": "sources",
                "sources": sources
            }
            
            # Generate and stream AI response
            full_response = ""
            async for chunk in self.gemini_client.generate_response_stream(
                request.message,
                context_documents,
                chat_history
            ):
                full_response += chunk
                yield {
                    "type": "content",
                    "content": chunk
                }
            
            # Save to history after streaming is complete
            await self.history_manager.add_message(
                request.user_name,
                "user",
                request.message
            )
            
            await self.history_manager.add_message(
                request.user_name,
                "assistant",
                full_response,
                {"sources": [doc.get("metadata", {}) for doc in context_documents]}
            )
            
            # Final done signal
            yield {
                "type": "done",
                "user_name": request.user_name
            }
            
        except Exception as e:
            logger.error(f"Error processing streaming chat request: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
