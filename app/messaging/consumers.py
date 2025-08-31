from aiokafka import AIOKafkaConsumer
import json
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
import uuid
from datetime import datetime

from ..database.factory import DatabaseFactory
from ..embeddings.manager import EmbeddingManager
from .schemas import DataIngestionMessage, EmbeddingMessage, VectorUpdateMessage, BatchStatusMessage
from .producer import KafkaProducer

logger = logging.getLogger(__name__)

class DataIngestionWorker:
    """Worker for processing data ingestion messages."""
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "ingestion-workers"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None
        self.running = False
        
    async def start(self):
        """Start the consumer worker."""
        try:
            # Initialize consumer
            self.consumer = AIOKafkaConsumer(
                'data-ingestion',
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            
            # Initialize producer for downstream messages
            self.producer = KafkaProducer(self.bootstrap_servers)
            await self.producer.start()
            
            await self.consumer.start()
            self.running = True
            
            logger.info(f"Data ingestion worker started with group_id: {self.group_id}")
            
            # Start consuming messages
            await self._consume_messages()
            
        except Exception as e:
            logger.error(f"Failed to start data ingestion worker: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the consumer worker."""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
        
        if self.producer:
            await self.producer.stop()
            
        logger.info("Data ingestion worker stopped")
    
    async def _consume_messages(self):
        """Main message consumption loop."""
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    # Parse message
                    ingestion_msg = DataIngestionMessage(**message.value)
                    logger.info(f"Processing ingestion batch: {ingestion_msg.batch_id}")
                    
                    # Process the ingestion request
                    await self._process_ingestion(ingestion_msg)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Could implement retry logic or dead letter queue here
                    
        except Exception as e:
            logger.error(f"Error in message consumption loop: {e}")
    
    async def _process_ingestion(self, message: DataIngestionMessage):
        """Process a single ingestion message."""
        batch_id = message.batch_id
        
        try:
            # Send initial status update
            await self.producer.send_batch_status(BatchStatusMessage(
                batch_id=batch_id,
                status="processing",
                timestamp=datetime.now()
            ))
            
            # Create database connector
            db_factory = DatabaseFactory()
            db_connector = await db_factory.create_connector(
                message.db_type,
                message.connection_params
            )
            
            total_docs = 0
            processed_docs = 0
            
            # Stream data from database and send embedding requests
            async for record in db_connector.get_data(
                message.table_or_collection,
                message.columns_or_fields
            ):
                total_docs += 1
                
                # Combine text fields for embedding
                text_parts = []
                for field in message.text_fields:
                    if field in record and record[field]:
                        text_parts.append(f"{field}: {record[field]}")
                
                combined_text = " | ".join(text_parts)
                
                if combined_text.strip():
                    # Send embedding request
                    embedding_msg = EmbeddingMessage(
                        document_id=str(record.get('id', uuid.uuid4())),
                        content=combined_text,
                        metadata=record,
                        batch_id=batch_id,
                        timestamp=datetime.now()
                    )
                    
                    await self.producer.send_embedding_request(embedding_msg)
                    processed_docs += 1
                
                # Send periodic status updates
                if total_docs % 100 == 0:
                    await self.producer.send_batch_status(BatchStatusMessage(
                        batch_id=batch_id,
                        status="processing",
                        total_documents=total_docs,
                        processed_documents=processed_docs,
                        timestamp=datetime.now()
                    ))
            
            # Cleanup database connection
            await db_connector.disconnect()
            
            # Send completion status
            await self.producer.send_batch_status(BatchStatusMessage(
                batch_id=batch_id,
                status="completed",
                total_documents=total_docs,
                processed_documents=processed_docs,
                timestamp=datetime.now()
            ))
            
            logger.info(f"Completed ingestion batch: {batch_id}, processed {processed_docs}/{total_docs} documents")
            
        except Exception as e:
            logger.error(f"Error processing ingestion batch {batch_id}: {e}")
            
            # Send failure status
            await self.producer.send_batch_status(BatchStatusMessage(
                batch_id=batch_id,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now()
            ))


class EmbeddingWorker:
    """Worker for processing embedding generation."""
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "embedding-workers"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None
        self.embedding_manager: Optional[EmbeddingManager] = None
        self.running = False
        
    async def start(self):
        """Start the embedding worker."""
        try:
            # Initialize embedding manager
            self.embedding_manager = EmbeddingManager()
            await self.embedding_manager.initialize()
            
            # Initialize consumer
            self.consumer = AIOKafkaConsumer(
                'embedding-requests',
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            
            # Initialize producer
            self.producer = KafkaProducer(self.bootstrap_servers)
            await self.producer.start()
            
            await self.consumer.start()
            self.running = True
            
            logger.info(f"Embedding worker started with group_id: {self.group_id}")
            
            # Start consuming messages
            await self._consume_messages()
            
        except Exception as e:
            logger.error(f"Failed to start embedding worker: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the embedding worker."""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
        
        if self.producer:
            await self.producer.stop()
        
        if self.embedding_manager:
            await self.embedding_manager.cleanup()
            
        logger.info("Embedding worker stopped")
    
    async def _consume_messages(self):
        """Main message consumption loop."""
        batch_buffer = {}  # Buffer documents by batch_id
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    # Parse message
                    embedding_msg = EmbeddingMessage(**message.value)
                    batch_id = embedding_msg.batch_id
                    
                    # Buffer documents by batch for batch processing
                    if batch_id not in batch_buffer:
                        batch_buffer[batch_id] = []
                    
                    batch_buffer[batch_id].append(embedding_msg)
                    
                    # Process batch when it reaches optimal size or timeout
                    if len(batch_buffer[batch_id]) >= 50:  # Process in batches of 50
                        await self._process_embedding_batch(batch_buffer[batch_id])
                        del batch_buffer[batch_id]
                        
                except Exception as e:
                    logger.error(f"Error processing embedding message: {e}")
                    
        except Exception as e:
            logger.error(f"Error in embedding consumption loop: {e}")
        
        # Process remaining documents in buffer
        for batch_docs in batch_buffer.values():
            if batch_docs:
                await self._process_embedding_batch(batch_docs)
    
    async def _process_embedding_batch(self, documents: list):
        """Process a batch of documents for embedding."""
        try:
            # Convert to format expected by embedding manager
            docs_for_embedding = []
            text_fields = ["content"]  # We already combined text fields
            
            for doc in documents:
                docs_for_embedding.append({
                    "id": doc.document_id,
                    "content": doc.content,
                    **doc.metadata
                })
            
            # Generate embeddings and store in ChromaDB
            num_added = await self.embedding_manager.add_documents(
                docs_for_embedding, 
                text_fields
            )
            
            logger.info(f"Processed {num_added} documents for embedding")
            
            # Send vector update messages
            for doc in documents:
                await self.producer.send_vector_update(VectorUpdateMessage(
                    operation="insert",
                    document_id=doc.document_id,
                    metadata=doc.metadata,
                    batch_id=doc.batch_id,
                    timestamp=datetime.now()
                ))
            
        except Exception as e:
            logger.error(f"Error processing embedding batch: {e}")
            # Could implement retry logic here
