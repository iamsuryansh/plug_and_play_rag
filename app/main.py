from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
import json
import uuid
from datetime import datetime

from .config import settings
from .models import ChatRequest, ChatResponse, DataSourceConfig, HealthResponse
from .database.factory import DatabaseFactory
from .embeddings.manager import EmbeddingManager
from .ai.gemini_client import GeminiClient
from .chat.history_manager import ChatHistoryManager
from .chat.rag_service import RAGService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Optional Kafka imports
try:
    from .messaging.producer import KafkaProducer
    from .messaging.status_tracker import RedisStatusTracker
    from .messaging.schemas import DataIngestionMessage, BatchStatusMessage
    KAFKA_AVAILABLE = True
    logger.info("Kafka dependencies available")
except ImportError:
    logger.warning("Kafka dependencies not available. Running without Kafka integration.")
    KafkaProducer = None
    RedisStatusTracker = None
    DataIngestionMessage = None
    BatchStatusMessage = None
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global services
embedding_manager = None
gemini_client = None
chat_history_manager = None
rag_service = None
kafka_producer = None
redis_tracker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    global embedding_manager, gemini_client, chat_history_manager, rag_service, kafka_producer, redis_tracker
    
    logger.info("Initializing application services...")
    
    try:
        # Initialize embedding manager
        embedding_manager = EmbeddingManager()
        await embedding_manager.initialize()
        
        # Initialize Gemini client
        gemini_client = GeminiClient(settings.GEMINI_API_KEY)
        
        # Initialize chat history manager
        chat_history_manager = ChatHistoryManager()
        
        # Initialize RAG service
        rag_service = RAGService(embedding_manager, gemini_client, chat_history_manager)
        
        # Initialize Kafka producer (optional - only if Kafka is available)
        if KAFKA_AVAILABLE:
            try:
                kafka_producer = KafkaProducer()
                await kafka_producer.start()
                logger.info("Kafka producer initialized")
            except Exception as e:
                logger.warning(f"Kafka producer initialization failed (will use synchronous processing): {e}")
                kafka_producer = None
        
        # Initialize Redis status tracker (optional - only if Redis is available)
        if KAFKA_AVAILABLE:
            try:
                redis_tracker = RedisStatusTracker()
                await redis_tracker.connect()
                logger.info("Redis status tracker initialized")
            except Exception as e:
                logger.warning(f"Redis status tracker initialization failed: {e}")
                redis_tracker = None
        
        logger.info("Application services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        logger.info("Shutting down application services...")
        if embedding_manager:
            await embedding_manager.cleanup()
        if kafka_producer:
            await kafka_producer.stop()
        if redis_tracker:
            await redis_tracker.disconnect()

app = FastAPI(
    title="Chat with Your Data",
    description="A RAG system that allows you to chat with your database data using AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
async def get_system_status():
    """
    Get comprehensive system status including all components.
    """
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "embedding_manager": embedding_manager is not None,
            "gemini_client": gemini_client is not None,
            "chat_history_manager": chat_history_manager is not None,
            "rag_service": rag_service is not None
        },
        "optional_services": {
            "kafka_available": KAFKA_AVAILABLE,
            "kafka_producer": kafka_producer is not None,
            "redis_tracker": redis_tracker is not None
        },
        "configuration": {
            "debug_mode": settings.DEBUG,
            "log_level": settings.LOG_LEVEL
        },
        "version": "1.0.0",
        "kafka_integration_ready": KAFKA_AVAILABLE and kafka_producer is not None
    }
    
    return status

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint returning API health status."""
    return HealthResponse(
        status="healthy",
        message="Chat with Your Data API is running",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="All services are operational",
        version="1.0.0"
    )

@app.post("/ingest-data-async")
async def ingest_data_async(config: DataSourceConfig):
    """
    Start asynchronous data ingestion using Kafka.
    Returns immediately with a batch ID for tracking progress.
    """
    if not KAFKA_AVAILABLE or not kafka_producer:
        raise HTTPException(
            status_code=503, 
            detail="Kafka is not available. Use /ingest-data for synchronous processing."
        )
    
    try:
        # Generate unique batch ID
        batch_id = str(uuid.uuid4())
        
        # Create ingestion message
        ingestion_msg = DataIngestionMessage(
            batch_id=batch_id,
            db_type=config.db_type,
            connection_params=config.connection_params,
            table_or_collection=config.table_or_collection,
            columns_or_fields=config.columns_or_fields,
            text_fields=config.text_fields,
            timestamp=datetime.now()
        )
        
        # Send message to Kafka
        await kafka_producer.send_ingestion_request(ingestion_msg)
        
        # Initialize status in Redis if available
        if redis_tracker:
            initial_status = BatchStatusMessage(
                batch_id=batch_id,
                status="queued",
                timestamp=datetime.now()
            )
            await redis_tracker.update_batch_status(initial_status)
        
        return {
            "message": "Data ingestion request queued successfully",
            "batch_id": batch_id,
            "status": "queued",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to queue data ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue data ingestion: {str(e)}")

@app.get("/ingest-status/{batch_id}")
async def get_ingestion_status(batch_id: str):
    """
    Get the status of an asynchronous ingestion job.
    """
    if not redis_tracker:
        raise HTTPException(
            status_code=503,
            detail="Status tracking is not available. Redis is not connected."
        )
    
    try:
        status = await redis_tracker.get_batch_status(batch_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} not found or has expired"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ingestion status: {str(e)}")

@app.get("/recent-batches")
async def get_recent_batches(limit: int = 20):
    """
    Get list of recent ingestion batches and their status.
    """
    if not redis_tracker:
        raise HTTPException(
            status_code=503,
            detail="Status tracking is not available. Redis is not connected."
        )
    
    try:
        batches = await redis_tracker.get_recent_batches(limit)
        return {"recent_batches": batches}
        
    except Exception as e:
        logger.error(f"Failed to get recent batches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent batches: {str(e)}")

@app.post("/ingest-data")
async def ingest_data(config: DataSourceConfig, background_tasks: BackgroundTasks):
    """
    Ingest data from a database table/collection and create embeddings.
    This runs in the background to avoid timeout issues.
    """
    try:
        # Validate database connection
        db_factory = DatabaseFactory()
        db_connector = await db_factory.create_connector(config.db_type, config.connection_params)
        
        # Add ingestion task to background
        background_tasks.add_task(
            rag_service.ingest_data_background,
            config
        )
        
        return {
            "message": "Data ingestion started in background",
            "status": "processing",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to start data ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start data ingestion: {str(e)}")

@app.post("/chat")
async def chat_with_data(request: ChatRequest):
    """
    Chat with your data using RAG approach.
    Returns a regular JSON response.
    """
    try:
        response = await rag_service.process_chat_request(request)
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/chat/stream")
async def chat_with_data_stream(request: ChatRequest):
    """
    Chat with your data using RAG approach with streaming response.
    """
    try:
        async def generate_stream() -> AsyncGenerator[str, None]:
            async for chunk in rag_service.process_chat_request_stream(request):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"Streaming chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming chat processing failed: {str(e)}")

@app.get("/chat/history/{user_name}")
async def get_chat_history(user_name: str, limit: int = 10):
    """Get chat history for a specific user."""
    try:
        history = await chat_history_manager.get_history(user_name, limit)
        return {"user_name": user_name, "history": history}
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@app.delete("/chat/history/{user_name}")
async def clear_chat_history(user_name: str):
    """Clear chat history for a specific user."""
    try:
        await chat_history_manager.clear_history(user_name)
        return {"message": f"Chat history cleared for user: {user_name}"}
        
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
