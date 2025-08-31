from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime

class DataIngestionMessage(BaseModel):
    """Message for data ingestion requests."""
    source_id: str = Field(..., description="Unique identifier for the data source")
    db_type: str = Field(..., description="Database type (postgresql/mongodb)")
    connection_params: Dict[str, Any] = Field(..., description="Database connection parameters")
    table_or_collection: str = Field(..., description="Table or collection name")
    columns_or_fields: List[str] = Field(..., description="Columns or fields to process")
    text_fields: List[str] = Field(..., description="Fields containing text for embeddings")
    batch_id: str = Field(..., description="Unique batch identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = Field(default=0, description="Number of retry attempts")

class EmbeddingMessage(BaseModel):
    """Message for embedding generation."""
    document_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Combined text content for embedding")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    batch_id: str = Field(..., description="Batch identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = Field(default=0, description="Number of retry attempts")

class VectorUpdateMessage(BaseModel):
    """Message for vector database updates."""
    operation: str = Field(..., description="Operation type: insert, update, delete")
    document_id: str = Field(..., description="Document identifier")
    vector: List[float] = Field(None, description="Embedding vector")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    batch_id: str = Field(..., description="Batch identifier")
    timestamp: datetime = Field(default_factory=datetime.now)

class BatchStatusMessage(BaseModel):
    """Message for batch status updates."""
    batch_id: str = Field(..., description="Batch identifier")
    status: str = Field(..., description="Status: queued, processing, completed, failed")
    total_documents: int = Field(default=0, description="Total documents in batch")
    processed_documents: int = Field(default=0, description="Processed documents count")
    failed_documents: int = Field(default=0, description="Failed documents count")
    error_message: str = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now)
