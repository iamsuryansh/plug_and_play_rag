from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
        # AI Configuration
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-pro", env="GEMINI_MODEL")
    GEMINI_TEMPERATURE: float = Field(default=0.7, env="GEMINI_TEMPERATURE")
    GEMINI_MAX_TOKENS: int = Field(default=8192, env="GEMINI_MAX_TOKENS")
    
    # LLM Configuration
    LLM_PROVIDER: str = Field(default="gemini", env="LLM_PROVIDER")
    LLM_MODEL_NAME: Optional[str] = Field(default=None, env="LLM_MODEL_NAME")
    LLM_ENDPOINT_URL: Optional[str] = Field(default=None, env="LLM_ENDPOINT_URL")
    LLM_API_KEY: Optional[str] = Field(default=None, env="LLM_API_KEY")
    
    # Ollama Configuration
    OLLAMA_ENDPOINT: str = Field(default="http://localhost:11434", env="OLLAMA_ENDPOINT")
    OLLAMA_MODEL: str = Field(default="llama2", env="OLLAMA_MODEL")
    
    # LM Studio Configuration  
    LMSTUDIO_ENDPOINT: str = Field(default="http://localhost:1234", env="LMSTUDIO_ENDPOINT")
    LMSTUDIO_MODEL: str = Field(default="local-model", env="LMSTUDIO_MODEL")
    
    # Kafka Configuration (optional)
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC: str = Field(default="chat_events", env="KAFKA_TOPIC")
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    COLLECTION_NAME: str = Field(default="documents", env="COLLECTION_NAME")
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    
    # MongoDB Configuration
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
    MONGO_USER: str = os.getenv("MONGO_USER", "")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "")
    MONGO_DB: str = os.getenv("MONGO_DB", "")
    MONGO_CONNECTION_STRING: Optional[str] = os.getenv("MONGO_CONNECTION_STRING")
    
    # Vector Database Configuration
    VECTOR_DB_COLLECTION: str = "document_embeddings"
    VECTOR_DB_PERSIST_DIR: str = "./chroma_db"
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
