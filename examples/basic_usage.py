"""
Basic usage examples for Chat with Your Data RAG system.
"""

import asyncio
import httpx

async def demo_basic_usage():
    """Demonstrate basic RAG system usage."""
    
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # 1. Check system health
        health = await client.get(f"{base_url}/health")
        print("System Health:", health.json())
        
        # 2. Ingest demo data
        ingest_config = {
            "db_type": "demo",
            "connection_params": {},
            "table_or_collection": "articles",
            "columns_or_fields": ["title", "content", "author"],
            "text_fields": ["title", "content"]
        }
        
        print("Ingesting demo data...")
        ingest_response = await client.post(
            f"{base_url}/ingest-data", 
            json=ingest_config
        )
        print("Ingestion Status:", ingest_response.json())
        
        # Wait for ingestion to complete
        await asyncio.sleep(5)
        
        # 3. Chat with your data
        chat_request = {
            "message": "What articles do you have about technology?",
            "user_name": "demo_user"
        }
        
        chat_response = await client.post(
            f"{base_url}/chat",
            json=chat_request
        )
        
        print("Chat Response:", chat_response.json())

if __name__ == "__main__":
    asyncio.run(demo_basic_usage())
