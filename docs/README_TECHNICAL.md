# README_TECHNICAL.md - Technical Implementation Details

## 🏗️ Architecture Deep Dive

### System Overview

The Chat with Your Data RAG system implements a sophisticated Retrieval-Augmented Generation architecture using modern Python async patterns, vector databases, and AI language models. The system is designed for production scalability, maintainability, and extensibility.

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Endpoints │  Swagger UI │  Streaming │  CORS      │
├─────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  RAG Service │ Chat History │ Background Tasks │ Lifecycle  │
├─────────────────────────────────────────────────────────────┤
│                     SERVICE LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  Embedding Manager │  Gemini AI Client │  Database Factory │
├─────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB │ PostgreSQL │ MongoDB │ Sentence Transformers   │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. FastAPI Application (`app/main.py`)

#### Async Lifecycle Management
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle with proper resource initialization and cleanup."""
```

**Key Features:**
- **Graceful Startup/Shutdown**: All services are initialized during startup and cleaned up on shutdown
- **Global Service Management**: Services are stored as global variables for dependency injection
- **Error Handling**: Comprehensive error handling during service initialization
- **CORS Support**: Configured for cross-origin requests

#### Endpoint Architecture
- **Health Checks**: `/health` and `/` endpoints for monitoring
- **Data Ingestion**: `/ingest-data` with background task processing
- **Chat Interface**: `/chat` (synchronous) and `/chat/stream` (asynchronous streaming)
- **History Management**: `/chat/history/{user_name}` for CRUD operations

### 2. Configuration Management (`app/config.py`)

#### Environment-Based Configuration
```python
class Settings(BaseSettings):
    """Pydantic-based configuration with automatic environment variable loading."""
```

**Features:**
- **Type Safety**: All configuration values are type-validated
- **Environment Variables**: Automatic `.env` file loading with `python-dotenv`
- **Default Values**: Sensible defaults for development
- **Validation**: Built-in validation for required fields

#### Configuration Categories:
- **API Settings**: Debug mode, logging levels
- **AI Configuration**: Gemini API key, model parameters
- **Database Settings**: Connection parameters for PostgreSQL and MongoDB
- **Vector Database**: ChromaDB configuration
- **Embedding Settings**: Model selection and chunking parameters

### 3. Database Layer

#### Abstract Base Class (`app/database/base.py`)
```python
class DatabaseConnector(ABC):
    """Abstract interface ensuring consistent behavior across database implementations."""
```

**Design Patterns:**
- **Abstract Factory Pattern**: Unified interface for different database types
- **Async Iterator Pattern**: Memory-efficient streaming of large datasets
- **Connection Management**: Automatic connection lifecycle management

#### PostgreSQL Connector (`app/database/postgresql.py`)
```python
class PostgreSQLConnector(DatabaseConnector):
    """Production-ready PostgreSQL connector with connection pooling."""
```

**Technical Implementation:**
- **Connection Pooling**: `asyncpg.create_pool()` with configurable min/max connections
- **Transaction Management**: Automatic transaction handling for data consistency
- **Cursor-Based Iteration**: Memory-efficient processing of large result sets
- **Schema Introspection**: Dynamic schema discovery using information_schema
- **Error Handling**: PostgreSQL-specific error handling and recovery

#### MongoDB Connector (`app/database/mongodb.py`)
```python
class MongoDBConnector(DatabaseConnector):
    """Async MongoDB connector with Motor driver."""
```

**Technical Implementation:**
- **Async Driver**: Motor (async wrapper for PyMongo)
- **Connection String Support**: Both individual parameters and connection strings
- **Projection Optimization**: Selective field retrieval to minimize data transfer
- **Document Streaming**: Async cursor iteration for memory efficiency
- **Schema Inference**: Dynamic field type discovery from sample documents

#### Database Factory (`app/database/factory.py`)
```python
class DatabaseFactory:
    """Factory pattern implementation for database connector instantiation."""
```

### 4. Embedding System (`app/embeddings/manager.py`)

#### Vector Database Integration
```python
class EmbeddingManager:
    """Manages ChromaDB integration and embedding generation."""
```

**Technical Architecture:**
- **Persistent Storage**: ChromaDB with configurable persistence directory
- **Sentence Transformers**: `all-MiniLM-L6-v2` model (384-dimensional embeddings)
- **Batch Processing**: Configurable batch sizes for memory optimization
- **Metadata Sanitization**: Automatic data cleaning for ChromaDB compatibility
- **Async Operations**: Non-blocking embedding generation using thread pools

#### Embedding Pipeline
1. **Text Combination**: Configurable field concatenation with field labels
2. **Metadata Cleaning**: List/dict conversion to ChromaDB-compatible formats
3. **Batch Processing**: Configurable batch sizes (default: 100 documents)
4. **Vector Generation**: Sentence transformer encoding in thread pools
5. **Storage**: ChromaDB insertion with automatic ID generation

#### Search Implementation
```python
async def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Semantic similarity search with relevance scoring."""
```

**Features:**
- **Cosine Similarity**: Default ChromaDB similarity metric
- **Result Ranking**: Distance-based relevance scoring
- **Configurable Results**: Adjustable result count per query
- **Rich Metadata**: Full document metadata preservation

### 5. AI Integration (`app/ai/gemini_client.py`)

#### Google Gemini Integration
```python
class GeminiClient:
    """Production-ready Gemini AI client with streaming support."""
```

**Technical Implementation:**
- **SDK Integration**: Official `google-generativeai` library
- **Async Wrapper**: Thread pool execution for blocking SDK calls
- **Streaming Support**: Real-time response generation
- **Error Handling**: Comprehensive error handling and retry logic
- **Configuration**: Flexible model and generation parameters

#### Prompt Engineering
```python
def _build_system_prompt(self) -> str:
    """Sophisticated system prompt for RAG optimization."""
```

**Prompt Structure:**
1. **Role Definition**: Clear assistant role and capabilities
2. **Context Instructions**: How to use retrieved documents
3. **Response Guidelines**: Formatting and citation requirements
4. **Data Handling**: Instructions for structured data interpretation
5. **Limitation Acknowledgment**: Transparent about knowledge boundaries

#### Context Assembly
```python
def _build_user_prompt(self, question: str, context_documents: List[Dict], chat_history: List[Dict]) -> str:
    """Dynamic context assembly with history integration."""
```

**Context Sections:**
- **Chat History**: Last 5 conversation turns for context continuity
- **Retrieved Documents**: Ranked relevant documents with metadata
- **Current Question**: User's immediate query
- **Formatting**: Clear section separation for AI comprehension

### 6. Chat Management

#### RAG Service (`app/chat/rag_service.py`)
```python
class RAGService:
    """Orchestrates the complete RAG pipeline."""
```

**Pipeline Implementation:**
1. **History Retrieval**: User-specific conversation history
2. **Context Search**: Semantic similarity search in vector database  
3. **AI Response**: Gemini generation with context and history
4. **History Persistence**: Automatic conversation logging
5. **Source Attribution**: Document source tracking and scoring

#### Streaming Implementation
```python
async def process_chat_request_stream(self, request: ChatRequest) -> AsyncIterator[Dict[str, Any]]:
    """Real-time streaming response generation."""
```

**Streaming Protocol:**
- **Source First**: Immediate source document delivery
- **Content Streaming**: Token-by-token response streaming
- **Completion Signal**: End-of-stream notification
- **Error Handling**: Graceful error propagation in stream

#### History Manager (`app/chat/history_manager.py`)
```python
class ChatHistoryManager:
    """In-memory chat history with user-based partitioning."""
```

**Features:**
- **User Isolation**: Separate conversation histories per user
- **Message Metadata**: Timestamps, roles, and additional context
- **Memory Management**: Configurable history limits
- **Thread Safety**: Async-safe operations

## 📊 Data Flow Architecture

### 1. Data Ingestion Flow
```
Database → DatabaseConnector → EmbeddingManager → ChromaDB
    ↓            ↓                    ↓             ↓
Raw Data → Structured Data → Text Embeddings → Vector Storage
```

**Process Steps:**
1. **Connection**: Database factory creates appropriate connector
2. **Streaming**: Async iteration over database records
3. **Batching**: Configurable batch processing (100 records/batch)
4. **Embedding**: Sentence transformer encoding
5. **Storage**: ChromaDB vector insertion with metadata

### 2. Query Processing Flow
```
User Query → Semantic Search → Context Assembly → AI Generation → Response
     ↓             ↓              ↓               ↓             ↓
  Question → Vector Search → Document Retrieval → Gemini API → Streamed Response
```

**Process Steps:**
1. **Query Embedding**: User question converted to vector
2. **Similarity Search**: ChromaDB cosine similarity search
3. **Context Assembly**: Retrieved documents + chat history
4. **Prompt Construction**: System + user prompt assembly
5. **AI Generation**: Gemini streaming response
6. **History Storage**: Conversation persistence

## 🔒 Security & Production Considerations

### 1. Authentication & Authorization
- **API Key Management**: Environment-based secret management
- **CORS Configuration**: Production-ready cross-origin settings
- **Input Validation**: Pydantic model validation for all endpoints
- **SQL Injection Prevention**: Parameterized queries in PostgreSQL connector

### 2. Error Handling
- **Layered Error Handling**: Service-specific error handling with fallbacks
- **Graceful Degradation**: System continues operating with component failures
- **Comprehensive Logging**: Structured logging with configurable levels
- **Client Error Responses**: User-friendly error messages with HTTP status codes

### 3. Performance Optimizations
- **Connection Pooling**: Database connection pools for concurrent requests
- **Async Operations**: Non-blocking I/O throughout the stack
- **Batch Processing**: Memory-efficient large dataset processing
- **Caching**: ChromaDB persistence for embedding reuse
- **Thread Pool Execution**: CPU-intensive operations offloaded to thread pools

### 4. Scalability Features
- **Background Tasks**: Non-blocking data ingestion
- **Streaming Responses**: Reduced client waiting time
- **Configurable Batch Sizes**: Memory usage optimization
- **Stateless Design**: Horizontal scaling capability
- **Service Separation**: Modular architecture for independent scaling

## 🧪 Testing & Development

### 1. Development Features
- **Hot Reload**: Automatic code reloading during development
- **Interactive Documentation**: Swagger UI and ReDoc
- **Demo Mode**: Database-free development and testing
- **Sample Data**: Comprehensive test datasets
- **Configuration Validation**: Startup-time configuration checking

### 2. Monitoring & Observability
- **Health Endpoints**: System health checking
- **Comprehensive Logging**: Request/response logging with timing
- **Error Tracking**: Detailed error logging with stack traces
- **Performance Metrics**: Database connection stats, embedding counts
- **Service Status**: Component initialization and health status

### 3. Extensibility Points
- **Database Connectors**: Plugin architecture for new database types
- **Embedding Models**: Configurable sentence transformer models
- **AI Providers**: Pluggable AI client implementations
- **Vector Databases**: Abstractable vector storage layer
- **Prompt Templates**: Customizable prompt engineering

## 📈 Performance Characteristics

### 1. Throughput Metrics
- **Embedding Generation**: ~100-1000 documents/minute (CPU-dependent)
- **Vector Search**: Sub-second response times for typical datasets
- **Concurrent Requests**: Supports multiple simultaneous users
- **Streaming Latency**: ~100ms first token time
- **Database Queries**: Connection pooling enables high concurrency

### 2. Memory Usage
- **Base Application**: ~200MB baseline memory usage
- **Embedding Model**: ~500MB for all-MiniLM-L6-v2 model
- **ChromaDB**: Configurable memory usage based on dataset size
- **Batch Processing**: Configurable memory vs. throughput trade-offs

### 3. Storage Requirements
- **Vector Storage**: ~1.5KB per document (384-dim embeddings + metadata)
- **Chat History**: In-memory storage (configurable persistence)
- **Model Cache**: ~500MB for sentence transformer model
- **Configuration**: Minimal storage for configuration files

## 🔧 Customization Guide

### 1. Adding New Database Connectors
```python
class CustomDBConnector(DatabaseConnector):
    """Template for new database connector implementation."""
    
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    async def get_data(self, table: str, columns: List[str]) -> AsyncIterator[Dict]:
        """Stream data from database."""
        pass
```

### 2. Custom Embedding Models
```python
# In app/config.py
EMBEDDING_MODEL = "your-custom-model-name"

# Model will be automatically loaded by EmbeddingManager
```

### 3. AI Provider Integration
```python
class CustomAIClient:
    """Template for new AI provider integration."""
    
    async def generate_response(self, prompt: str) -> str:
        """Generate AI response."""
        pass
    
    async def generate_response_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate streaming AI response."""
        pass
```

### 4. Custom Prompt Templates
```python
def custom_system_prompt() -> str:
    """Custom system prompt for domain-specific applications."""
    return "Your custom prompt here..."
```

## 🚀 Kafka Integration (Recommended Enhancement)

### Why Add Kafka?

The current system processes data ingestion synchronously, which can become a bottleneck for large datasets or real-time applications. Kafka would transform this into an event-driven, horizontally scalable architecture.

#### Current Architecture Limitations:
- **Synchronous Processing**: Data ingestion blocks until completion
- **Single Point Processing**: No horizontal scaling for embeddings
- **No Real-time Updates**: Manual re-ingestion required for data changes
- **Resource Constraints**: Memory and CPU bottlenecks during large ingestions

### Enhanced Architecture with Kafka

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN RAG SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                      DATA SOURCES                          │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL │ MongoDB │ File Systems │ APIs │ Webhooks     │
│      │           │           │          │        │          │
│      └───────────┼───────────┼──────────┼────────┘          │
├─────────────────────────────────────────────────────────────┤
│                      KAFKA LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Data Ingestion Topic │ Embedding Topic │ Update Topic     │
│         │                     │               │              │
├─────────────────────────────────────────────────────────────┤
│                   CONSUMER SERVICES                        │
├─────────────────────────────────────────────────────────────┤
│  Ingestion Workers │ Embedding Workers │ Update Handlers   │
│         │                     │               │              │
├─────────────────────────────────────────────────────────────┤
│              VECTOR DATABASE & CHAT LAYER                  │
├─────────────────────────────────────────────────────────────┤
│     ChromaDB │ Chat History │ RAG Service │ FastAPI        │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Strategy

#### 1. **Kafka Topics Design**
```python
# Topic Configuration
KAFKA_TOPICS = {
    "data-ingestion": {
        "partitions": 12,
        "replication_factor": 3,
        "retention_ms": 86400000  # 24 hours
    },
    "embedding-requests": {
        "partitions": 8,
        "replication_factor": 3,
        "retention_ms": 3600000   # 1 hour
    },
    "vector-updates": {
        "partitions": 4,
        "replication_factor": 3,
        "retention_ms": 86400000  # 24 hours
    }
}
```

#### 2. **Message Schema**
```python
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

class DataIngestionMessage(BaseModel):
    """Message for data ingestion requests."""
    source_id: str
    db_type: str
    connection_params: Dict[str, Any]
    table_or_collection: str
    columns_or_fields: List[str]
    text_fields: List[str]
    batch_id: str
    timestamp: datetime
    
class EmbeddingMessage(BaseModel):
    """Message for embedding generation."""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    batch_id: str
    timestamp: datetime
    
class VectorUpdateMessage(BaseModel):
    """Message for vector database updates."""
    operation: str  # "insert", "update", "delete"
    document_id: str
    vector: List[float]
    metadata: Dict[str, Any]
    timestamp: datetime
```

#### 3. **Kafka Producer Integration**
```python
from aiokafka import AIOKafkaProducer
import json

class KafkaProducer:
    """Async Kafka producer for data pipeline."""
    
    def __init__(self, bootstrap_servers: str):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type="snappy",
            batch_size=16384,
            linger_ms=10
        )
    
    async def send_ingestion_request(self, message: DataIngestionMessage):
        """Send data ingestion request to Kafka."""
        await self.producer.send(
            'data-ingestion',
            value=message.dict(),
            key=message.source_id.encode('utf-8')
        )
    
    async def send_embedding_request(self, message: EmbeddingMessage):
        """Send embedding generation request."""
        await self.producer.send(
            'embedding-requests',
            value=message.dict(),
            key=message.document_id.encode('utf-8')
        )
```

#### 4. **Kafka Consumer Workers**
```python
from aiokafka import AIOKafkaConsumer

class DataIngestionWorker:
    """Worker for processing data ingestion messages."""
    
    async def start(self):
        consumer = AIOKafkaConsumer(
            'data-ingestion',
            bootstrap_servers=self.kafka_servers,
            group_id="ingestion-workers",
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        async for message in consumer:
            try:
                await self.process_ingestion(message.value)
            except Exception as e:
                # Handle errors, send to DLQ
                logger.error(f"Ingestion failed: {e}")
    
    async def process_ingestion(self, data: dict):
        """Process single ingestion message."""
        # Create database connector
        # Stream data and send to embedding topic
        # Handle batching and error recovery
        pass

class EmbeddingWorker:
    """Worker for processing embedding generation."""
    
    async def start(self):
        consumer = AIOKafkaConsumer(
            'embedding-requests',
            bootstrap_servers=self.kafka_servers,
            group_id="embedding-workers",
            auto_offset_reset='earliest'
        )
        
        async for message in consumer:
            try:
                await self.generate_embeddings(message.value)
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
    
    async def generate_embeddings(self, data: dict):
        """Generate embeddings and store in vector DB."""
        # Generate embeddings using sentence transformers
        # Store in ChromaDB
        # Send update confirmation
        pass
```

#### 5. **Modified FastAPI Endpoints**
```python
@app.post("/ingest-data-async")
async def ingest_data_async(config: DataSourceConfig):
    """Async data ingestion via Kafka."""
    
    # Validate configuration
    # Generate batch ID
    # Send message to Kafka
    
    message = DataIngestionMessage(
        source_id=f"{config.db_type}_{config.table_or_collection}",
        db_type=config.db_type,
        connection_params=config.connection_params,
        table_or_collection=config.table_or_collection,
        columns_or_fields=config.columns_or_fields,
        text_fields=config.text_fields,
        batch_id=str(uuid.uuid4()),
        timestamp=datetime.now()
    )
    
    await kafka_producer.send_ingestion_request(message)
    
    return {
        "message": "Data ingestion request queued",
        "batch_id": message.batch_id,
        "status": "queued"
    }

@app.get("/ingest-status/{batch_id}")
async def get_ingestion_status(batch_id: str):
    """Get status of ingestion batch."""
    # Query processing status from Redis/database
    # Return progress, completion status, error details
    pass
```

### Benefits of Kafka Integration

#### 1. **Performance Improvements**
- **Parallel Processing**: Multiple workers processing different partitions
- **Horizontal Scaling**: Add more consumer instances as needed
- **Batch Optimization**: Configurable batch sizes for optimal throughput
- **Resource Efficiency**: CPU and memory usage distributed across workers

#### 2. **Reliability & Monitoring**
- **Message Persistence**: No data loss during system failures
- **Replay Capability**: Reprocess failed batches
- **Consumer Group Management**: Automatic partition rebalancing
- **Dead Letter Queues**: Handle permanently failed messages

#### 3. **Real-time Capabilities**
- **Change Data Capture**: Real-time database change streaming
- **Incremental Updates**: Only process changed documents
- **Event Sourcing**: Complete audit trail of all operations
- **Live Synchronization**: Keep vector database in sync with source data

#### 4. **Operational Benefits**
- **Status Monitoring**: Track ingestion progress in real-time
- **Error Handling**: Centralized error processing and retry logic
- **Load Balancing**: Distribute work across multiple instances
- **Graceful Degradation**: System continues operating during partial failures

### Implementation Priority

#### Phase 1: Basic Kafka Integration
1. Add Kafka producer to FastAPI endpoints
2. Implement basic consumer for data ingestion
3. Add status tracking for batch processing

#### Phase 2: Advanced Features
1. Multiple consumer groups for parallel processing
2. Dead letter queue handling
3. Metrics and monitoring integration

#### Phase 3: Real-time Synchronization
1. Database change data capture
2. Incremental embedding updates
3. Event-driven architecture completion

### Recommended Stack
- **Apache Kafka**: Message broker
- **aiokafka**: Async Python Kafka client
- **Kafka Connect**: Database CDC connectors
- **Redis**: Status tracking and caching
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## � Kafka Integration (Event-Driven Architecture)

### Message Queue System

The system now supports distributed, scalable data processing through Kafka integration:

#### Kafka Topics
- **data-ingestion**: Data ingestion requests from API
- **embedding-requests**: Documents to be processed for embeddings
- **vector-updates**: ChromaDB update notifications
- **batch-status**: Processing status updates

#### Consumer Workers
- **DataIngestionWorker**: Extracts data from databases and publishes to embedding queue
- **EmbeddingWorker**: Generates embeddings and updates ChromaDB
- **KafkaStatusConsumer**: Updates batch processing status in Redis

#### New API Endpoints
- **POST /ingest-data-async**: Queue data for asynchronous processing
- **GET /ingest-status/{batch_id}**: Check processing status
- **GET /recent-batches**: View recent ingestion batches

#### Message Schema (`app/messaging/schemas.py`)
```python
class DataIngestionMessage(BaseModel):
    batch_id: str
    db_type: str
    connection_params: Dict[str, Any]
    table_or_collection: str
    columns_or_fields: List[str]
    text_fields: List[str]
    timestamp: datetime

class BatchStatusMessage(BaseModel):
    batch_id: str
    status: str  # queued, processing, completed, failed
    total_documents: Optional[int]
    processed_documents: Optional[int]
    error_message: Optional[str]
    timestamp: datetime
```

#### Redis Status Tracking
- **Batch Status**: Real-time progress tracking
- **Recent Batches**: Sorted set of recent processing jobs
- **TTL Management**: Automatic cleanup of old status records

### Running with Kafka

#### Using Docker Compose (Recommended)
```bash
# Start infrastructure
docker-compose up -d

# Start the application
./start.sh
```

#### Manual Setup
```bash
# Start Kafka and Redis
docker-compose up -d kafka redis

# Install dependencies
pip install -r requirements.txt

# Start API server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start worker processes
python run_workers.py
```

#### Configuration
```env
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis Configuration  
REDIS_URL=redis://localhost:6379

# Worker Configuration
INGESTION_WORKERS=2
EMBEDDING_WORKERS=3
```

## �📚 Dependencies & Versions

### Core Framework
- **FastAPI**: Modern, high-performance web framework
- **Uvicorn**: ASGI server with auto-reload
- **Pydantic**: Data validation and settings management

### Database Drivers
- **asyncpg**: High-performance PostgreSQL async driver
- **motor**: Async MongoDB driver

### AI & ML Libraries
- **google-generativeai**: Official Gemini AI SDK
- **sentence-transformers**: State-of-the-art embedding models
- **chromadb**: Vector database for similarity search

### Message Queue & Caching
- **aiokafka**: Async Kafka client for Python
- **redis**: Redis client for status tracking
- **httpx**: HTTP client for testing

### Utility Libraries
- **python-dotenv**: Environment variable management
- **aiofiles**: Async file operations
- **python-multipart**: Form data handling

## 🚀 Deployment Architecture

### Production Setup
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │────│    FastAPI API   │────│   Kafka Cluster │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Redis Cluster  │    │  Worker Nodes   │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   ChromaDB      │    │   PostgreSQL    │
                       └─────────────────┘    └─────────────────┘
```

This technical documentation provides comprehensive implementation details for developers who need to understand, maintain, or extend the Chat with Your Data RAG system with Kafka integration.

```
