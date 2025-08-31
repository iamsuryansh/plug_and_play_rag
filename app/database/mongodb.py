from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any, AsyncIterator
import logging
from ..database.base import DatabaseConnector

logger = logging.getLogger(__name__)

class MongoDBConnector(DatabaseConnector):
    """MongoDB database connector."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.client = None
        self.database = None
    
    async def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            # Check if connection string is provided
            if "connection_string" in self.connection_params:
                connection_string = self.connection_params["connection_string"]
            else:
                # Build connection string from parameters
                host = self.connection_params.get("host", "localhost")
                port = self.connection_params.get("port", 27017)
                user = self.connection_params.get("user")
                password = self.connection_params.get("password")
                
                if user and password:
                    connection_string = f"mongodb://{user}:{password}@{host}:{port}/"
                else:
                    connection_string = f"mongodb://{host}:{port}/"
            
            self.client = AsyncIOMotorClient(connection_string)
            self.database = self.client[self.connection_params.get("database")]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("MongoDB connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def get_data(
        self,
        table_or_collection: str,
        columns_or_fields: List[str],
        limit: int = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Retrieve data from MongoDB collection."""
        if not self.database:
            await self.connect()
        
        try:
            collection = self.database[table_or_collection]
            
            # Create projection for specified fields
            projection = {field: 1 for field in columns_or_fields}
            projection["_id"] = 0  # Exclude _id field by default
            
            cursor = collection.find({}, projection)
            
            if limit:
                cursor = cursor.limit(limit)
            
            async for document in cursor:
                yield document
                
        except Exception as e:
            logger.error(f"Error retrieving data from MongoDB: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test MongoDB connection."""
        try:
            if not self.client:
                await self.connect()
            
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            return False
    
    async def get_schema(self, table_or_collection: str) -> Dict[str, str]:
        """Get MongoDB collection schema (field types from sample documents)."""
        if not self.database:
            await self.connect()
        
        try:
            collection = self.database[table_or_collection]
            
            # Get a sample document to infer schema
            sample_doc = await collection.find_one()
            if not sample_doc:
                return {}
            
            schema = {}
            for key, value in sample_doc.items():
                if key == "_id":
                    continue
                schema[key] = type(value).__name__
            
            return schema
            
        except Exception as e:
            logger.error(f"Error getting MongoDB schema: {e}")
            raise
