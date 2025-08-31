from typing import Dict, Any
from ..models import DatabaseType
from ..database.base import DatabaseConnector
from ..database.postgresql import PostgreSQLConnector
from ..database.mongodb import MongoDBConnector

class DatabaseFactory:
    """Factory class for creating database connectors."""
    
    @staticmethod
    async def create_connector(
        db_type: DatabaseType,
        connection_params: Dict[str, Any]
    ) -> DatabaseConnector:
        """
        Create and return appropriate database connector.
        
        Args:
            db_type: Type of database (postgresql or mongodb)
            connection_params: Connection parameters
            
        Returns:
            Initialized database connector
        """
        if db_type == DatabaseType.POSTGRESQL:
            connector = PostgreSQLConnector(connection_params)
        elif db_type == DatabaseType.MONGODB:
            connector = MongoDBConnector(connection_params)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        await connector.connect()
        return connector
