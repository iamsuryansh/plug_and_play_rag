from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator

class DatabaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def get_data(
        self,
        table_or_collection: str,
        columns_or_fields: List[str],
        limit: int = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Retrieve data from the specified table/collection.
        
        Args:
            table_or_collection: Name of table (PostgreSQL) or collection (MongoDB)
            columns_or_fields: List of columns/fields to retrieve
            limit: Maximum number of records to retrieve
            
        Yields:
            Dict containing record data
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connection is working."""
        pass
    
    @abstractmethod
    async def get_schema(self, table_or_collection: str) -> Dict[str, str]:
        """
        Get schema information for the specified table/collection.
        
        Returns:
            Dict mapping column/field names to their types
        """
        pass
