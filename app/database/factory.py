from typing import Dict, Any
from ..models import DatabaseType, CSVConfig
from ..database.base import DatabaseConnector
from ..database.postgresql import PostgreSQLConnector
from ..database.mongodb import MongoDBConnector
from ..database.csv_connector import CSVConnector

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
            db_type: Type of database (postgresql, mongodb, or csv)
            connection_params: Connection parameters
            
        Returns:
            Initialized database connector
        """
        if db_type == DatabaseType.POSTGRESQL:
            connector = PostgreSQLConnector(connection_params)
        elif db_type == DatabaseType.MONGODB:
            connector = MongoDBConnector(connection_params)
        elif db_type == DatabaseType.CSV:
            # For CSV, connection_params should contain CSV configuration
            csv_config = CSVConfig(**connection_params)
            connector = CSVConnector(csv_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        await connector.connect()
        return connector
