import asyncpg
from typing import List, Dict, Any, AsyncIterator
import logging
from ..database.base import DatabaseConnector

logger = logging.getLogger(__name__)

class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.connection = None
        self.pool = None
    
    async def connect(self) -> None:
        """Establish PostgreSQL connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.connection_params.get("host", "localhost"),
                port=self.connection_params.get("port", 5432),
                user=self.connection_params.get("user"),
                password=self.connection_params.get("password"),
                database=self.connection_params.get("database"),
                min_size=1,
                max_size=10
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def get_data(
        self,
        table_or_collection: str,
        columns_or_fields: List[str],
        limit: int = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Retrieve data from PostgreSQL table."""
        if not self.pool:
            await self.connect()
        
        # Build SQL query
        columns_str = ", ".join(columns_or_fields)
        query = f"SELECT {columns_str} FROM {table_or_collection}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            async with self.pool.acquire() as connection:
                logger.info(f"Executing query: {query}")
                async with connection.transaction():
                    async for record in connection.cursor(query):
                        yield dict(record)
        except Exception as e:
            logger.error(f"Error retrieving data from PostgreSQL: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test PostgreSQL connection."""
        try:
            if not self.pool:
                await self.connect()
            
            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False
    
    async def get_schema(self, table_or_collection: str) -> Dict[str, str]:
        """Get PostgreSQL table schema."""
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """
        
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(query, table_or_collection)
                return {row['column_name']: row['data_type'] for row in rows}
        except Exception as e:
            logger.error(f"Error getting PostgreSQL schema: {e}")
            raise
