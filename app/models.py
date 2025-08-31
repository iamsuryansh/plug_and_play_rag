from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime

class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"

class DataSourceConfig(BaseModel):
    """Configuration for data source connection."""
    db_type: DatabaseType
    connection_params: Dict[str, Any]
    table_or_collection: str
    columns_or_fields: List[str] = Field(..., description="Fields to use for embeddings")
    text_fields: List[str] = Field(..., description="Fields containing text data")
    
class ChatRequest(BaseModel):
    """Request model for chat endpoints."""
    user_name: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., min_length=1, description="User's question or message")
    max_results: Optional[int] = Field(5, description="Maximum number of context documents to retrieve")
    include_history: bool = Field(True, description="Whether to include chat history in context")
    
class ChatMessage(BaseModel):
    """Individual chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    
class ChatResponse(BaseModel):
    """Response model for chat endpoints."""
    user_name: str
    response: str
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used for context")
    timestamp: datetime = Field(default_factory=datetime.now)
    
class StreamChunk(BaseModel):
    """Streaming response chunk."""
    type: str = Field(..., description="Type of chunk: 'content', 'sources', 'done'")
    content: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    version: str
    
class IngestionStatus(BaseModel):
    """Data ingestion status."""
    status: str
    message: str
    records_processed: Optional[int] = None
    embeddings_created: Optional[int] = None
    error: Optional[str] = None
