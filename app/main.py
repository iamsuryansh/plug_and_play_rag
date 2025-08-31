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
from .models import (
    ChatRequest, ChatResponse, DataSourceConfig, 
    HealthResponse, IngestionStatus, StreamChunk,
    CSVConfig, CSVColumnConfig, CSVColumnType
)
from .database.factory import DatabaseFactory
from .embeddings.manager import EmbeddingManager
from .ai.llm_factory import LLMFactory
from .ai.base_client import BaseLLMClient
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
        
        # Initialize LLM client
        logger.info(f"Initializing {settings.LLM_PROVIDER} LLM client...")
        if settings.LLM_PROVIDER.lower() == "gemini":
            llm_client = LLMFactory.create_client(
                provider="gemini",
                api_key=settings.GEMINI_API_KEY
            )
        elif settings.LLM_PROVIDER.lower() == "ollama":
            llm_client = LLMFactory.create_client(
                provider="ollama",
                model_name=settings.OLLAMA_MODEL,
                endpoint_url=settings.OLLAMA_ENDPOINT
            )
        elif settings.LLM_PROVIDER.lower() == "lmstudio":
            llm_client = LLMFactory.create_client(
                provider="lmstudio",
                model_name=settings.LMSTUDIO_MODEL,
                endpoint_url=settings.LMSTUDIO_ENDPOINT
            )
        else:
            # Use custom configuration
            llm_client = LLMFactory.create_client(
                provider=settings.LLM_PROVIDER,
                model_name=settings.LLM_MODEL_NAME,
                endpoint_url=settings.LLM_ENDPOINT_URL,
                api_key=settings.LLM_API_KEY
            )
        
        # For backward compatibility, set both variables
        gemini_client = llm_client
        
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
    title="Plug-and-Play RAG API",
    description="Universal RAG system supporting multiple databases and LLM providers",
    version="1.0.0",
    docs_url="/docs",
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
        message="Plug-and-Play RAG API is running - Connect any database to any LLM!",
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

@app.get("/api/llm/providers")
async def get_llm_providers():
    """Get information about supported LLM providers."""
    return LLMFactory.get_supported_providers()

@app.get("/api/llm/current")
async def get_current_llm():
    """Get information about the current LLM provider."""
    if not gemini_client:
        raise HTTPException(status_code=503, detail="No LLM client available")
    
    try:
        info = gemini_client.get_client_info()
        return {
            "provider": info.get("type"),
            "model": info.get("model"),
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting LLM info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving LLM information")

@app.post("/api/llm/switch")
async def switch_llm_provider(request: dict):
    """Switch to a different LLM provider temporarily (for this session)."""
    global gemini_client, rag_service
    
    try:
        provider = request.get("provider")
        model_name = request.get("model_name")
        endpoint_url = request.get("endpoint_url")
        api_key = request.get("api_key")
        
        if not provider:
            raise HTTPException(status_code=400, detail="Provider is required")
        
        # Create new client
        new_client = LLMFactory.create_client(
            provider=provider,
            model_name=model_name,
            endpoint_url=endpoint_url,
            api_key=api_key
        )
        
        # Test the new client
        test_response = await new_client.generate_response(
            "Test message",
            context="This is a test to verify the LLM client is working."
        )
        
        # If test passes, switch to new client
        gemini_client = new_client
        
        # Update RAG service with new client
        if rag_service:
            rag_service.llm_client = new_client
        
        info = new_client.get_client_info()
        return {
            "status": "success",
            "message": f"Switched to {provider}",
            "provider": info.get("type"),
            "model": info.get("model"),
            "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error switching LLM provider: {e}")
        raise HTTPException(status_code=500, detail="Error switching LLM provider")

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

@app.post("/ingest-csv")
async def ingest_csv_data(csv_config: CSVConfig, background_tasks: BackgroundTasks):
    """
    Ingest data from a CSV file and create embeddings.
    This runs in the background to avoid timeout issues.
    """
    try:
        # Validate CSV file and configuration
        from pathlib import Path
        if not Path(csv_config.file_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_config.file_path}")
        
        # Create DataSourceConfig for CSV
        config = DataSourceConfig(
            db_type="csv",
            connection_params=csv_config.model_dump(),
            table_or_collection="csv_data",  # Not used for CSV
            columns_or_fields=csv_config.text_columns,
            text_fields=csv_config.text_columns
        )
        
        # Add ingestion task to background
        background_tasks.add_task(
            rag_service.ingest_data_background,
            config
        )
        
        return {
            "message": "CSV data ingestion started in background",
            "status": "processing",
            "file_path": csv_config.file_path,
            "text_columns": csv_config.text_columns,
            "config": config.model_dump()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions  
        raise
    except Exception as e:
        logger.error(f"Failed to start CSV data ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start CSV data ingestion: {str(e)}")

@app.post("/validate-csv")
async def validate_csv_config(csv_config: CSVConfig):
    """
    Validate CSV configuration and return schema information.
    """
    try:
        from .database.csv_connector import CSVConnector
        
        # Create and test CSV connector
        connector = CSVConnector(csv_config)
        await connector.connect()
        
        # Get schema information
        schema_info = connector.get_schema_info()
        
        await connector.disconnect()
        
        return {
            "status": "valid",
            "message": "CSV configuration is valid",
            "schema_info": schema_info
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate CSV configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate CSV configuration: {str(e)}")

@app.get("/csv-sample/{file_path:path}")
async def get_csv_sample(file_path: str, rows: int = 5):
    """
    Get a sample of rows from CSV file for configuration assistance.
    """
    try:
        import pandas as pd
        from pathlib import Path
        
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {file_path}")
        
        # Read sample rows
        df_sample = pd.read_csv(file_path, nrows=rows)
        
        # Convert to records and handle NaN values
        sample_records = []
        for _, row in df_sample.iterrows():
            record = {}
            for key, value in row.items():
                if pd.isna(value):
                    record[key] = None
                else:
                    record[key] = value
            sample_records.append(record)
        
        return {
            "file_path": file_path,
            "columns": list(df_sample.columns),
            "sample_rows": sample_records,
            "total_columns": len(df_sample.columns),
            "sample_size": len(sample_records)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found: {file_path}")
    except Exception as e:
        logger.error(f"Failed to read CSV sample: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read CSV sample: {str(e)}")

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
