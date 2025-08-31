"""
Configuration management for Plug-and-Play RAG system
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from app.models import DatabaseType, CSVColumnConfig, CSVColumnType


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(..., description="LLM provider (gemini, openai, ollama, lmstudio, custom)")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    api_url: Optional[str] = Field(None, description="Custom API URL for local/custom providers")
    model_name: str = Field("gemini-pro", description="Model name to use")
    temperature: float = Field(0.7, description="Temperature for text generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    
    # Custom provider settings
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom headers for API requests")
    request_format: Optional[Dict[str, Any]] = Field(None, description="Custom request format")
    response_format: Optional[Dict[str, Any]] = Field(None, description="Custom response format")


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    type: DatabaseType = Field(..., description="Database type")
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    
    # Additional connection parameters
    connection_params: Optional[Dict[str, Any]] = Field(None, description="Additional connection parameters")
    
    @validator('host', 'port', 'database', 'username', 'password')
    def validate_db_params(cls, v, values, field):
        """Validate required database parameters based on type."""
        db_type = values.get('type')
        if db_type in [DatabaseType.POSTGRESQL, DatabaseType.MONGODB] and v is None:
            if field.name != 'password':  # Password can be None for some setups
                raise ValueError(f"{field.name} is required for {db_type} databases")
        return v


class CSVDataSourceConfig(BaseModel):
    """CSV data source configuration."""
    name: str = Field(..., description="Unique name for this CSV source")
    file_path: str = Field(..., description="Path to CSV file (relative to data/ directory)")
    delimiter: str = Field(",", description="CSV delimiter")
    has_header: bool = Field(True, description="Whether CSV has header row")
    encoding: str = Field("utf-8", description="File encoding")
    
    # Column configurations
    columns: List[CSVColumnConfig] = Field(..., description="Column configurations")
    text_columns: List[str] = Field(..., description="Columns to use for text embeddings")
    metadata_columns: Optional[List[str]] = Field(None, description="Columns to include as metadata")
    
    # Processing options
    chunk_size: int = Field(1000, description="Number of rows to process at once")
    skip_rows: int = Field(0, description="Number of rows to skip from beginning")
    max_rows: Optional[int] = Field(None, description="Maximum number of rows to process")


class DatabaseDataSourceConfig(BaseModel):
    """Database data source configuration."""
    name: str = Field(..., description="Unique name for this database source")
    database_config: str = Field(..., description="Reference to database config name")
    table_or_collection: str = Field(..., description="Table or collection name")
    columns_or_fields: List[str] = Field(..., description="Fields to retrieve")
    text_fields: List[str] = Field(..., description="Fields containing text data")
    query_filter: Optional[Dict[str, Any]] = Field(None, description="Additional query filters")


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    model_name: str = Field("all-MiniLM-L6-v2", description="Sentence transformer model name")
    max_seq_length: int = Field(512, description="Maximum sequence length")
    device: str = Field("cpu", description="Device to run embeddings on (cpu/cuda)")
    batch_size: int = Field(32, description="Batch size for embedding generation")


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    type: str = Field("chromadb", description="Vector DB type (currently only chromadb)")
    collection_name: str = Field("rag_documents", description="Collection name")
    persist_directory: str = Field("./chroma_db", description="Persistence directory")
    similarity_threshold: float = Field(0.7, description="Similarity threshold for retrieval")
    max_results: int = Field(10, description="Maximum results to retrieve")


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(False, description="Auto-reload on code changes")
    workers: int = Field(1, description="Number of worker processes")
    log_level: str = Field("info", description="Log level")


class PlugAndPlayConfig(BaseModel):
    """Main configuration for Plug-and-Play RAG system."""
    # System info
    app_name: str = Field("Plug-and-Play RAG", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    description: str = Field("Retrieval-Augmented Generation system with multiple data sources", description="App description")
    
    # Core configurations
    llm: LLMConfig = Field(..., description="LLM configuration")
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig, description="Embedding configuration")
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig, description="Vector database configuration")
    server: ServerConfig = Field(default_factory=ServerConfig, description="Server configuration")
    
    # Data sources
    databases: Optional[Dict[str, DatabaseConfig]] = Field(None, description="Database configurations")
    csv_sources: Optional[List[CSVDataSourceConfig]] = Field(None, description="CSV data sources")
    database_sources: Optional[List[DatabaseDataSourceConfig]] = Field(None, description="Database data sources")
    
    # Processing options
    auto_ingest_on_startup: bool = Field(True, description="Automatically ingest data on startup")
    batch_processing: bool = Field(True, description="Enable batch processing for large datasets")
    enable_chat_history: bool = Field(True, description="Enable chat history management")
    
    # Optional features
    enable_streaming: bool = Field(True, description="Enable streaming responses")
    enable_cors: bool = Field(True, description="Enable CORS")
    cors_origins: List[str] = Field(["*"], description="Allowed CORS origins")


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: str = "config/app_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[PlugAndPlayConfig] = None
    
    def load_config(self) -> PlugAndPlayConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        # Load YAML or JSON config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            elif self.config_path.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")
        
        # Parse and validate
        self.config = PlugAndPlayConfig(**config_data)
        return self.config
    
    def get_config(self) -> PlugAndPlayConfig:
        """Get loaded configuration."""
        if self.config is None:
            return self.load_config()
        return self.config
    
    def create_sample_config(self, output_path: str = "config/app_config.yaml"):
        """Create a sample configuration file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        sample_config = {
            "app_name": "Plug-and-Play RAG",
            "version": "1.0.0",
            "description": "Retrieval-Augmented Generation system with multiple data sources",
            
            "llm": {
                "provider": "gemini",
                "api_key": "${GEMINI_API_KEY}",  # Environment variable
                "model_name": "gemini-pro",
                "temperature": 0.7
            },
            
            "embedding": {
                "model_name": "all-MiniLM-L6-v2",
                "device": "cpu",
                "batch_size": 32
            },
            
            "vector_db": {
                "type": "chromadb",
                "collection_name": "rag_documents",
                "persist_directory": "/app/data/chroma_db",
                "similarity_threshold": 0.7,
                "max_results": 10
            },
            
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": False,
                "workers": 1,
                "log_level": "info"
            },
            
            "databases": {
                "postgres_main": {
                    "type": "postgresql",
                    "host": "${DB_HOST}",
                    "port": 5432,
                    "database": "${DB_NAME}",
                    "username": "${DB_USER}",
                    "password": "${DB_PASSWORD}"
                }
            },
            
            "csv_sources": [
                {
                    "name": "sample_articles",
                    "file_path": "sample_data.csv",
                    "delimiter": ",",
                    "has_header": True,
                    "encoding": "utf-8",
                    "columns": [
                        {
                            "name": "title",
                            "type": "text",
                            "required": True
                        },
                        {
                            "name": "content", 
                            "type": "text",
                            "required": True
                        },
                        {
                            "name": "category",
                            "type": "text",
                            "required": False
                        }
                    ],
                    "text_columns": ["title", "content"],
                    "metadata_columns": ["category"],
                    "chunk_size": 1000
                }
            ],
            
            "database_sources": [
                {
                    "name": "articles_table",
                    "database_config": "postgres_main",
                    "table_or_collection": "articles",
                    "columns_or_fields": ["title", "content", "category"],
                    "text_fields": ["title", "content"]
                }
            ],
            
            "auto_ingest_on_startup": True,
            "batch_processing": True,
            "enable_chat_history": True,
            "enable_streaming": True,
            "enable_cors": True,
            "cors_origins": ["*"]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        
        print(f"Sample configuration created at: {output_path}")
        return output_path
    
    def validate_data_files(self) -> List[str]:
        """Validate that all referenced data files exist."""
        missing_files = []
        
        if self.config and self.config.csv_sources:
            data_dir = Path("data")
            for csv_source in self.config.csv_sources:
                file_path = data_dir / csv_source.file_path
                if not file_path.exists():
                    missing_files.append(str(file_path))
        
        return missing_files
    
    def resolve_environment_variables(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in configuration."""
        import re
        
        def replace_env_vars(obj):
            if isinstance(obj, str):
                # Replace ${VAR} patterns with environment variables
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, obj)
                for match in matches:
                    env_value = os.getenv(match, "")
                    obj = obj.replace(f"${{{match}}}", env_value)
                return obj
            elif isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            return obj
        
        return replace_env_vars(config_dict)


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> PlugAndPlayConfig:
    """Get the current configuration."""
    return config_manager.get_config()


def load_config_from_file(config_path: str) -> PlugAndPlayConfig:
    """Load configuration from a specific file."""
    manager = ConfigManager(config_path)
    return manager.load_config()
