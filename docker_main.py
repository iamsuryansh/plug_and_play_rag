"""
Docker-compatible main application file with configuration-driven initialization
"""

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.manager import ConfigManager, get_config
from app.config.app import initialize_app, get_app
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.models import CSVConfig, DataSourceConfig, DatabaseType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/app.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Plug-and-Play RAG application...")
    
    try:
        # Initialize configuration and services
        config_path = os.getenv("CONFIG_PATH", "/app/config/app_config.yaml")
        app_instance = await initialize_app(config_path)
        config = app_instance.get_config()
        
        logger.info(f"Application '{config.app_name}' v{config.version} started successfully")
        logger.info(f"Server running on {config.server.host}:{config.server.port}")
        
        # Store in app state
        app.state.app_instance = app_instance
        app.state.config = config
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    
    # Shutdown
    logger.info("Shutting down Plug-and-Play RAG application...")
    if hasattr(app.state, 'app_instance'):
        await app.state.app_instance.shutdown()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application with configuration."""
    # Load basic config to get app info
    try:
        config = get_config()
    except:
        # Use defaults if config not available yet
        config = None
    
    app = FastAPI(
        title=config.app_name if config else "Plug-and-Play RAG",
        version=config.version if config else "1.0.0",
        description=config.description if config else "Configuration-driven RAG system",
        lifespan=lifespan
    )
    
    return app


# Create the FastAPI app
app = create_app()


# Add middleware after app creation
@app.middleware("http")
async def add_cors_middleware(request, call_next):
    """Add CORS middleware based on configuration."""
    response = await call_next(request)
    
    if hasattr(app.state, 'config') and app.state.config.enable_cors:
        origins = app.state.config.cors_origins
        if "*" in origins or str(request.headers.get("origin")) in origins:
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    config = getattr(app.state, 'config', None)
    
    return HealthResponse(
        status="healthy",
        message="All services are operational",
        version=config.version if config else "1.0.0"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint using configured RAG service."""
    try:
        if not hasattr(app.state, 'app_instance'):
            raise HTTPException(status_code=503, detail="Application not initialized")
        
        rag_service = app.state.app_instance.get_rag_service()
        config = app.state.config
        
        # Process chat request
        response = await rag_service.process_chat(
            user_name=request.user_name,
            message=request.message,
            max_results=request.max_results,
            include_history=request.include_history and config.enable_chat_history
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat endpoint."""
    try:
        if not hasattr(app.state, 'app_instance'):
            raise HTTPException(status_code=503, detail="Application not initialized")
        
        config = app.state.config
        if not config.enable_streaming:
            raise HTTPException(status_code=503, detail="Streaming is disabled in configuration")
        
        rag_service = app.state.app_instance.get_rag_service()
        
        # Create streaming generator
        async def generate_stream():
            async for chunk in rag_service.stream_chat(
                user_name=request.user_name,
                message=request.message,
                max_results=request.max_results,
                include_history=request.include_history and config.enable_chat_history
            ):
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming chat failed: {str(e)}")


@app.post("/ingest-csv")
async def ingest_csv_endpoint(csv_config: CSVConfig, background_tasks: BackgroundTasks):
    """Ingest CSV data endpoint."""
    try:
        if not hasattr(app.state, 'app_instance'):
            raise HTTPException(status_code=503, detail="Application not initialized")
        
        # Validate file exists (in Docker container context)
        file_path = Path("/app/data") / csv_config.file_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_config.file_path}")
        
        rag_service = app.state.app_instance.get_rag_service()
        
        # Create data source config
        data_source_config = DataSourceConfig(
            db_type=DatabaseType.CSV,
            connection_params=csv_config.model_dump(),
            table_or_collection="csv_data",
            columns_or_fields=csv_config.text_columns,
            text_fields=csv_config.text_columns
        )
        
        # Add to background tasks
        background_tasks.add_task(
            rag_service.ingest_data_background,
            data_source_config
        )
        
        return {
            "status": "processing",
            "message": "CSV data ingestion started",
            "file_path": csv_config.file_path,
            "text_columns": csv_config.text_columns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"CSV ingestion failed: {str(e)}")


@app.get("/config/info")
async def config_info():
    """Get current configuration information."""
    try:
        if not hasattr(app.state, 'config'):
            raise HTTPException(status_code=503, detail="Configuration not loaded")
        
        config = app.state.config
        
        return {
            "app_name": config.app_name,
            "version": config.version,
            "description": config.description,
            "llm_provider": config.llm.provider,
            "llm_model": config.llm.model_name,
            "embedding_model": config.embedding.model_name,
            "vector_db": config.vector_db.type,
            "features": {
                "chat_history": config.enable_chat_history,
                "streaming": config.enable_streaming,
                "cors": config.enable_cors,
                "auto_ingest": config.auto_ingest_on_startup
            },
            "data_sources": {
                "csv_sources": len(config.csv_sources) if config.csv_sources else 0,
                "database_sources": len(config.database_sources) if config.database_sources else 0,
                "databases": len(config.databases) if config.databases else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get config info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config info: {str(e)}")


def main():
    """Main entry point for Docker container."""
    try:
        # Create config directories
        os.makedirs("/app/config", exist_ok=True)
        os.makedirs("/app/data", exist_ok=True)
        os.makedirs("/app/logs", exist_ok=True)
        
        # Check if config file exists
        config_path = os.getenv("CONFIG_PATH", "/app/config/app_config.yaml")
        if not Path(config_path).exists():
            logger.error(f"Configuration file not found: {config_path}")
            logger.info("Creating sample configuration...")
            
            # Create sample config
            manager = ConfigManager()
            manager.create_sample_config(config_path)
            logger.info(f"Sample configuration created at: {config_path}")
            logger.info("Please edit the configuration file and restart the container")
            sys.exit(1)
        
        # Load config for server settings
        config = get_config()
        server_config = config.server
        
        # Run the server
        uvicorn.run(
            app,
            host=server_config.host,
            port=server_config.port,
            reload=server_config.reload,
            workers=server_config.workers,
            log_level=server_config.log_level,
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
