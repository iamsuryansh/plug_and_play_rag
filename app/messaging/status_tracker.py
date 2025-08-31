import redis.asyncio as aioredis
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .schemas import BatchStatusMessage

logger = logging.getLogger(__name__)

class RedisStatusTracker:
    """Redis-based status tracking for batch processing."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis for status tracking")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def update_batch_status(self, status_msg: BatchStatusMessage):
        """Update batch status in Redis."""
        if not self.redis_client:
            await self.connect()
        
        try:
            # Store status with expiration (24 hours)
            status_data = {
                "batch_id": status_msg.batch_id,
                "status": status_msg.status,
                "total_documents": status_msg.total_documents or 0,
                "processed_documents": status_msg.processed_documents or 0,
                "error_message": status_msg.error_message,
                "timestamp": status_msg.timestamp.isoformat(),
                "progress_percentage": self._calculate_progress(
                    status_msg.processed_documents or 0,
                    status_msg.total_documents or 0
                )
            }
            
            await self.redis_client.setex(
                f"batch_status:{status_msg.batch_id}",
                86400,  # 24 hours TTL
                json.dumps(status_data, default=str)
            )
            
            # Also store in a sorted set for recent batches
            await self.redis_client.zadd(
                "recent_batches",
                {status_msg.batch_id: status_msg.timestamp.timestamp()}
            )
            
            logger.debug(f"Updated status for batch {status_msg.batch_id}: {status_msg.status}")
            
        except Exception as e:
            logger.error(f"Failed to update batch status in Redis: {e}")
            raise
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch status from Redis."""
        if not self.redis_client:
            await self.connect()
        
        try:
            status_data = await self.redis_client.get(f"batch_status:{batch_id}")
            if status_data:
                return json.loads(status_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get batch status from Redis: {e}")
            return None
    
    async def get_recent_batches(self, limit: int = 50) -> list:
        """Get list of recent batch IDs."""
        if not self.redis_client:
            await self.connect()
        
        try:
            # Get recent batch IDs from sorted set (most recent first)
            batch_ids = await self.redis_client.zrevrange("recent_batches", 0, limit - 1)
            
            # Get status for each batch
            batches = []
            for batch_id in batch_ids:
                status = await self.get_batch_status(batch_id)
                if status:
                    batches.append(status)
            
            return batches
        except Exception as e:
            logger.error(f"Failed to get recent batches from Redis: {e}")
            return []
    
    def _calculate_progress(self, processed: int, total: int) -> float:
        """Calculate progress percentage."""
        if total == 0:
            return 0.0
        return round((processed / total) * 100, 2)


class KafkaStatusConsumer:
    """Consumer specifically for batch status messages."""
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        redis_tracker: Optional[RedisStatusTracker] = None
    ):
        self.bootstrap_servers = bootstrap_servers
        self.redis_tracker = redis_tracker or RedisStatusTracker()
        self.consumer = None
        self.running = False
        
    async def start(self):
        """Start the status consumer."""
        try:
            from aiokafka import AIOKafkaConsumer
            
            # Initialize consumer
            self.consumer = AIOKafkaConsumer(
                'batch-status',
                bootstrap_servers=self.bootstrap_servers,
                group_id='status-trackers',
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            
            await self.consumer.start()
            await self.redis_tracker.connect()
            
            self.running = True
            logger.info("Status consumer started")
            
            # Start consuming messages
            await self._consume_status_messages()
            
        except Exception as e:
            logger.error(f"Failed to start status consumer: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the status consumer."""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
        
        await self.redis_tracker.disconnect()
        logger.info("Status consumer stopped")
    
    async def _consume_status_messages(self):
        """Consume and process status messages."""
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    # Parse status message
                    status_msg = BatchStatusMessage(**message.value)
                    
                    # Update status in Redis
                    await self.redis_tracker.update_batch_status(status_msg)
                    
                except Exception as e:
                    logger.error(f"Error processing status message: {e}")
                    
        except Exception as e:
            logger.error(f"Error in status consumption loop: {e}")
