from aiokafka import AIOKafkaProducer
import json
import logging
from typing import Optional
from ..config import settings
from .schemas import DataIngestionMessage, EmbeddingMessage, VectorUpdateMessage, BatchStatusMessage

logger = logging.getLogger(__name__)

class KafkaProducer:
    """Async Kafka producer for data pipeline messaging."""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        
    async def start(self):
        """Initialize and start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type="snappy",
                batch_size=16384,
                linger_ms=10,
                acks='all',  # Wait for all replicas to acknowledge
                retries=5,
                retry_backoff_ms=300
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def send_ingestion_request(self, message: DataIngestionMessage) -> str:
        """Send data ingestion request to Kafka."""
        try:
            if not self.producer:
                raise ValueError("Producer not started")
                
            await self.producer.send(
                topic='data-ingestion',
                value=message.dict(),
                key=message.source_id
            )
            logger.info(f"Sent ingestion request for batch: {message.batch_id}")
            return message.batch_id
            
        except Exception as e:
            logger.error(f"Failed to send ingestion request: {e}")
            raise
    
    async def send_embedding_request(self, message: EmbeddingMessage) -> None:
        """Send embedding generation request."""
        try:
            if not self.producer:
                raise ValueError("Producer not started")
                
            await self.producer.send(
                topic='embedding-requests',
                value=message.dict(),
                key=message.document_id
            )
            logger.debug(f"Sent embedding request for document: {message.document_id}")
            
        except Exception as e:
            logger.error(f"Failed to send embedding request: {e}")
            raise
    
    async def send_vector_update(self, message: VectorUpdateMessage) -> None:
        """Send vector database update message."""
        try:
            if not self.producer:
                raise ValueError("Producer not started")
                
            await self.producer.send(
                topic='vector-updates',
                value=message.dict(),
                key=message.document_id
            )
            logger.debug(f"Sent vector update for document: {message.document_id}")
            
        except Exception as e:
            logger.error(f"Failed to send vector update: {e}")
            raise
    
    async def send_batch_status(self, message: BatchStatusMessage) -> None:
        """Send batch status update."""
        try:
            if not self.producer:
                raise ValueError("Producer not started")
                
            await self.producer.send(
                topic='batch-status',
                value=message.dict(),
                key=message.batch_id
            )
            logger.info(f"Sent batch status update: {message.batch_id} - {message.status}")
            
        except Exception as e:
            logger.error(f"Failed to send batch status: {e}")
            raise
