#!/usr/bin/env python3
"""
Worker management script for Kafka consumers.
This script manages multiple worker processes for data ingestion and embedding generation.
"""

import asyncio
import logging
import signal
import sys
from typing import List
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.messaging.consumers import DataIngestionWorker, EmbeddingWorker
from app.messaging.status_tracker import KafkaStatusConsumer
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class WorkerManager:
    """Manages multiple Kafka consumer workers."""
    
    def __init__(self):
        self.workers: List = []
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Worker counts
        self.ingestion_workers = int(os.getenv("INGESTION_WORKERS", "2"))
        self.embedding_workers = int(os.getenv("EMBEDDING_WORKERS", "3"))
        
    async def start_workers(self):
        """Start all worker processes."""
        logger.info("Starting Kafka consumer workers...")
        
        try:
            # Start data ingestion workers
            for i in range(self.ingestion_workers):
                worker = DataIngestionWorker(
                    bootstrap_servers=self.kafka_servers,
                    group_id=f"ingestion-workers-{i}"
                )
                self.workers.append(worker)
                asyncio.create_task(worker.start())
                logger.info(f"Started data ingestion worker {i}")
            
            # Start embedding workers
            for i in range(self.embedding_workers):
                worker = EmbeddingWorker(
                    bootstrap_servers=self.kafka_servers,
                    group_id=f"embedding-workers-{i}"
                )
                self.workers.append(worker)
                asyncio.create_task(worker.start())
                logger.info(f"Started embedding worker {i}")
            
            # Start status consumer
            status_consumer = KafkaStatusConsumer(self.kafka_servers)
            self.workers.append(status_consumer)
            asyncio.create_task(status_consumer.start())
            logger.info("Started status consumer")
            
            logger.info(f"All workers started successfully. Total: {len(self.workers)}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Failed to start workers: {e}")
            raise
        finally:
            await self.stop_workers()
    
    async def stop_workers(self):
        """Stop all worker processes."""
        logger.info("Stopping all workers...")
        
        # Stop all workers concurrently
        stop_tasks = []
        for worker in self.workers:
            stop_tasks.append(asyncio.create_task(worker.stop()))
        
        if stop_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*stop_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some workers did not stop gracefully within timeout")
        
        logger.info("All workers stopped")
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()


async def main():
    """Main function to run worker management."""
    manager = WorkerManager()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, manager.handle_shutdown)
    signal.signal(signal.SIGTERM, manager.handle_shutdown)
    
    try:
        await manager.start_workers()
    except KeyboardInterrupt:
        logger.info("Shutdown initiated by user")
    except Exception as e:
        logger.error(f"Worker manager failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)
