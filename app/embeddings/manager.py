import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging
import asyncio
import uuid
import json
from ..config import settings

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manages embeddings and vector database operations."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.persist_directory = settings.VECTOR_DB_PERSIST_DIR
        self.collection_name = settings.VECTOR_DB_COLLECTION
    
    async def initialize(self) -> None:
        """Initialize the embedding manager."""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Document embeddings for RAG system"}
            )
            
            # Initialize embedding model
            await self._initialize_embedding_model()
            
            logger.info(f"EmbeddingManager initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingManager: {e}")
            raise
    
    async def _initialize_embedding_model(self) -> None:
        """Initialize the sentence transformer model."""
        def load_model():
            return SentenceTransformer(self.model_name)
        
        # Load model in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.embedding_model = await loop.run_in_executor(None, load_model)
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        text_fields: List[str]
    ) -> int:
        """
        Add documents to the vector database.
        
        Args:
            documents: List of document dictionaries
            text_fields: Fields to use for creating embeddings
            
        Returns:
            Number of documents added
        """
        if not self.collection or not self.embedding_model:
            raise ValueError("EmbeddingManager not properly initialized")
        
        try:
            texts = []
            metadatas = []
            ids = []
            
            for doc in documents:
                # Combine text fields for embedding
                combined_text = self._combine_text_fields(doc, text_fields)
                if not combined_text.strip():
                    continue
                
                texts.append(combined_text)
                metadatas.append(self._clean_metadata(doc))
                ids.append(str(uuid.uuid4()))
            
            if not texts:
                logger.warning("No valid texts found for embedding")
                return 0
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(texts)
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} documents to vector database")
            return len(texts)
            
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {e}")
            raise
    
    async def search_similar(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents based on query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        if not self.collection or not self.embedding_model:
            raise ValueError("EmbeddingManager not properly initialized")
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(n_results, self.collection.count())
            )
            
            # Format results
            similar_docs = []
            if results['documents'][0]:  # Check if results exist
                for i in range(len(results['documents'][0])):
                    doc = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results.get('distances') else None,
                        'id': results['ids'][0][i]
                    }
                    similar_docs.append(doc)
            
            logger.info(f"Found {len(similar_docs)} similar documents for query")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            raise
    
    def _combine_text_fields(self, document: Dict[str, Any], text_fields: List[str]) -> str:
        """Combine specified text fields into a single string."""
        combined_parts = []
        
        for field in text_fields:
            if field in document and document[field] is not None:
                value = str(document[field]).strip()
                if value:
                    combined_parts.append(f"{field}: {value}")
        
        return " | ".join(combined_parts)
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata to ensure compatibility with ChromaDB."""
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, (list, tuple)):
                # Convert lists/tuples to comma-separated strings
                cleaned[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Convert dictionaries to JSON strings
                cleaned[key] = json.dumps(value)
            elif value is None:
                # Skip None values
                continue
            else:
                # Keep primitive types as-is
                cleaned[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
        return cleaned
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using sentence transformer."""
        def encode_texts():
            return self.embedding_model.encode(texts, convert_to_tensor=False).tolist()
        
        # Generate embeddings in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, encode_texts)
        return embeddings
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # ChromaDB client doesn't need explicit cleanup
        logger.info("EmbeddingManager cleanup completed")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection."""
        if not self.collection:
            return {"error": "Collection not initialized"}
        
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "model_name": self.model_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
