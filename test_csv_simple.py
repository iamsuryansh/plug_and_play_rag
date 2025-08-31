#!/usr/bin/env python3
"""
Simple CSV ingestion test without requiring LLM API key
"""

import requests
import json
from pathlib import Path


def test_csv_functionality():
    """Test CSV functionality without requiring API key."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing CSV Functionality")
    print("=" * 50)
    
    # 1. Test server health
    print("1. Checking server health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Server is healthy")
            print(f"   Status: {health_data.get('status')}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # 2. Test CSV sample endpoint
    print("\n2. Testing CSV sample endpoint...")
    csv_file = Path("sample_data.csv").resolve()
    try:
        response = requests.get(f"{base_url}/csv-sample/{csv_file}?rows=3", timeout=10)
        if response.status_code == 200:
            sample_data = response.json()
            print("✅ CSV sample endpoint works")
            print(f"   Columns found: {len(sample_data['columns'])}")
            print(f"   Sample rows: {len(sample_data['sample_rows'])}")
            print(f"   First column: {sample_data['columns'][0]}")
        else:
            print(f"❌ CSV sample failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ CSV sample request failed: {e}")
        return False
    
    # 3. Test CSV validation
    print("\n3. Testing CSV validation...")
    csv_config = {
        "file_path": str(csv_file),
        "delimiter": ",",
        "has_header": True,
        "encoding": "utf-8",
        "columns": [
            {"name": "title", "type": "text", "required": True},
            {"name": "content", "type": "text", "required": True},
            {"name": "category", "type": "text", "required": False},
            {"name": "author", "type": "text", "required": False},
            {"name": "publication_date", "type": "text", "required": False},
            {"name": "tags", "type": "text", "required": False}
        ],
        "text_columns": ["title", "content"],
        "metadata_columns": ["category", "author", "publication_date", "tags"],
        "chunk_size": 100
    }
    
    try:
        response = requests.post(f"{base_url}/validate-csv", json=csv_config, timeout=10)
        if response.status_code == 200:
            validation_data = response.json()
            print("✅ CSV validation works")
            print(f"   Status: {validation_data.get('status')}")
            schema = validation_data.get('schema_info', {})
            print(f"   Total rows: {schema.get('total_rows')}")
            print(f"   Total columns: {schema.get('total_columns')}")
        else:
            print(f"❌ CSV validation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ CSV validation request failed: {e}")
        return False
    
    # 4. Test CSV ingestion endpoint (without LLM)
    print("\n4. Testing CSV ingestion endpoint...")
    try:
        response = requests.post(f"{base_url}/ingest-csv", json=csv_config, timeout=30)
        if response.status_code == 200:
            ingestion_data = response.json()
            print("✅ CSV ingestion endpoint works")
            print(f"   Status: {ingestion_data.get('status')}")
            print(f"   Message: {ingestion_data.get('message')}")
            print(f"   File: {Path(ingestion_data.get('file_path', '')).name}")
        else:
            print(f"❌ CSV ingestion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ CSV ingestion request failed: {e}")
        return False
    
    print("\n✅ All CSV functionality tests passed!")
    print("\nNotes:")
    print("- CSV data ingestion is working correctly")
    print("- To test full chat functionality, configure GEMINI_API_KEY")
    print("- The ingested data is ready for semantic search")
    
    return True


if __name__ == "__main__":
    success = test_csv_functionality()
    exit(0 if success else 1)
