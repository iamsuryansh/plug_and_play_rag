#!/usr/bin/env python3
"""
CSV Data Ingestion Demo for Plug-and-Play RAG

This script demonstrates how to ingest CSV data into the RAG system.
It shows configuration of column types, text fields, and metadata.
"""

import asyncio
import httpx
import json
from pathlib import Path

# CSV configuration for the sample data
CSV_CONFIG = {
    "file_path": "sample_data.csv",
    "delimiter": ",",
    "has_header": True,
    "encoding": "utf-8",
    "columns": [
        {
            "name": "title",
            "type": "text",
            "required": True,
            "description": "Article title"
        },
        {
            "name": "content", 
            "type": "text",
            "required": True,
            "description": "Main article content"
        },
        {
            "name": "category",
            "type": "text",
            "required": False,
            "description": "Article category"
        },
        {
            "name": "author",
            "type": "text",
            "required": False,
            "description": "Article author"
        },
        {
            "name": "publication_date",
            "type": "datetime",
            "required": False,
            "description": "Publication date"
        },
        {
            "name": "tags",
            "type": "text",
            "required": False,
            "description": "Comma-separated tags"
        }
    ],
    "text_columns": ["title", "content"],  # Columns to use for embeddings
    "metadata_columns": ["category", "author", "publication_date", "tags"],  # Metadata to store
    "chunk_size": 100,
    "skip_rows": 0,
    "max_rows": None
}

async def demo_csv_ingestion():
    """Demonstrate CSV data ingestion."""
    print("🚀 Plug-and-Play RAG - CSV Data Ingestion Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Check if server is running
            print("1. Checking server health...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Server is running")
                health_data = response.json()
                print(f"   Version: {health_data.get('version', 'unknown')}")
            else:
                print("❌ Server not responding")
                return
            
            # 2. Get CSV sample to verify structure
            print("\n2. Getting CSV sample...")
            file_path = Path("sample_data.csv").resolve()
            response = await client.get(f"{base_url}/csv-sample/{file_path}")
            if response.status_code == 200:
                sample_data = response.json()
                print("✅ CSV sample retrieved")
                print(f"   Columns: {sample_data['columns']}")
                print(f"   Sample rows: {len(sample_data['sample_rows'])}")
                print("   First row sample:")
                if sample_data['sample_rows']:
                    for key, value in list(sample_data['sample_rows'][0].items())[:3]:
                        print(f"     {key}: {str(value)[:50]}...")
            else:
                print(f"❌ Failed to get CSV sample: {response.status_code}")
                return
            
            # 3. Validate CSV configuration
            print("\n3. Validating CSV configuration...")
            response = await client.post(
                f"{base_url}/validate-csv",
                json=CSV_CONFIG
            )
            if response.status_code == 200:
                validation_data = response.json()
                print("✅ CSV configuration is valid")
                schema_info = validation_data.get('schema_info', {})
                print(f"   Total rows: {schema_info.get('total_rows', 'unknown')}")
                print(f"   Total columns: {schema_info.get('total_columns', 'unknown')}")
                print(f"   Text columns: {CSV_CONFIG['text_columns']}")
                print(f"   Metadata columns: {CSV_CONFIG.get('metadata_columns', [])}")
            else:
                print(f"❌ CSV configuration validation failed: {response.status_code}")
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                return
            
            # 4. Start CSV data ingestion
            print("\n4. Starting CSV data ingestion...")
            response = await client.post(
                f"{base_url}/ingest-csv",
                json=CSV_CONFIG
            )
            if response.status_code == 200:
                ingestion_data = response.json()
                print("✅ CSV ingestion started successfully")
                print(f"   Status: {ingestion_data.get('status', 'unknown')}")
                print(f"   File: {ingestion_data.get('file_path', 'unknown')}")
                print(f"   Text columns: {ingestion_data.get('text_columns', [])}")
                print("   Processing in background...")
            else:
                print(f"❌ Failed to start CSV ingestion: {response.status_code}")
                return
            
            # 5. Wait a bit for processing
            print("\n5. Waiting for ingestion to complete...")
            await asyncio.sleep(5)
            
            # 6. Test chat with ingested data
            print("\n6. Testing chat with CSV data...")
            chat_request = {
                "message": "What is machine learning?",
                "user_name": "csv_demo_user"
            }
            response = await client.post(
                f"{base_url}/chat",
                json=chat_request
            )
            if response.status_code == 200:
                chat_data = response.json()
                print("✅ Chat response received")
                print(f"   Response: {chat_data.get('response', 'No response')[:200]}...")
                sources = chat_data.get('sources', [])
                if sources:
                    print(f"   Sources found: {len(sources)}")
                    for i, source in enumerate(sources[:2]):
                        print(f"     Source {i+1}: {source.get('metadata', {}).get('category', 'Unknown')}")
                else:
                    print("   No sources found (data might still be processing)")
            else:
                print(f"❌ Chat request failed: {response.status_code}")
            
            # 7. Test another query
            print("\n7. Testing another query...")
            chat_request = {
                "message": "Tell me about deep learning and neural networks",
                "user_name": "csv_demo_user"
            }
            response = await client.post(
                f"{base_url}/chat",
                json=chat_request
            )
            if response.status_code == 200:
                chat_data = response.json()
                print("✅ Second chat response received")
                print(f"   Response: {chat_data.get('response', 'No response')[:200]}...")
                sources = chat_data.get('sources', [])
                print(f"   Sources found: {len(sources)}")
            
            print("\n🎉 CSV ingestion demo completed successfully!")
            print("\nYou can now:")
            print("- Ask questions about the CSV data")
            print("- Ingest additional CSV files")
            print("- Mix CSV data with database sources")
            
        except httpx.TimeoutException:
            print("❌ Request timeout. Make sure the server is running on localhost:8001")
        except httpx.ConnectError:
            print("❌ Connection error. Make sure the server is running on localhost:8001")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def print_configuration_example():
    """Print example configuration for different CSV scenarios."""
    print("\n📋 CSV Configuration Examples")
    print("=" * 50)
    
    print("\n1. Simple CSV with title and content:")
    simple_config = {
        "file_path": "articles.csv",
        "columns": [
            {"name": "title", "type": "text", "required": True},
            {"name": "body", "type": "text", "required": True}
        ],
        "text_columns": ["title", "body"]
    }
    print(json.dumps(simple_config, indent=2))
    
    print("\n2. Complex CSV with different data types:")
    complex_config = {
        "file_path": "products.csv",
        "columns": [
            {"name": "name", "type": "text", "required": True},
            {"name": "description", "type": "text", "required": True},
            {"name": "price", "type": "float", "required": True},
            {"name": "in_stock", "type": "boolean", "default_value": False},
            {"name": "created_date", "type": "datetime"},
            {"name": "features", "type": "json"}
        ],
        "text_columns": ["name", "description"],
        "metadata_columns": ["price", "in_stock", "created_date", "features"]
    }
    print(json.dumps(complex_config, indent=2))

async def main():
    """Main demo function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "examples":
        print_configuration_example()
        return
    
    # Check if sample CSV exists
    if not Path("sample_data.csv").exists():
        print("❌ Sample CSV file not found!")
        print("Make sure 'sample_data.csv' exists in the current directory.")
        return
    
    await demo_csv_ingestion()

if __name__ == "__main__":
    asyncio.run(main())
