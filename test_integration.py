#!/usr/bin/env python3
"""
Test script for Kafka integration.
This script tests the complete async data ingestion pipeline.
"""

import asyncio
import httpx
import json
import time
import sys
from pathlib import Path

# Add the app directory to the path  
sys.path.insert(0, str(Path(__file__).parent))

from app.messaging.producer import KafkaProducer
from app.messaging.status_tracker import RedisStatusTracker

async def test_kafka_integration():
    """Test the complete Kafka integration."""
    print("🧪 Testing Kafka Integration...")
    
    # Test 1: Test Kafka producer directly
    print("\n1. Testing Kafka Producer...")
    try:
        producer = KafkaProducer()
        await producer.start()
        print("✅ Kafka producer started successfully")
        await producer.stop()
        print("✅ Kafka producer stopped successfully")
    except Exception as e:
        print(f"❌ Kafka producer test failed: {e}")
        return False
    
    # Test 2: Test Redis status tracker
    print("\n2. Testing Redis Status Tracker...")
    try:
        redis_tracker = RedisStatusTracker()
        await redis_tracker.connect()
        
        # Test status update
        from app.messaging.schemas import BatchStatusMessage
        from datetime import datetime
        
        test_status = BatchStatusMessage(
            batch_id="test-batch-123",
            status="testing",
            timestamp=datetime.now()
        )
        
        await redis_tracker.update_batch_status(test_status)
        
        # Test status retrieval
        status = await redis_tracker.get_batch_status("test-batch-123")
        if status and status["status"] == "testing":
            print("✅ Redis status tracking works")
        else:
            print("❌ Redis status tracking failed")
            return False
            
        await redis_tracker.disconnect()
        
    except Exception as e:
        print(f"❌ Redis status tracker test failed: {e}")
        return False
    
    # Test 3: Test API endpoints
    print("\n3. Testing API Endpoints...")
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ Health endpoint works")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test async ingestion endpoint (if available)
            test_config = {
                "db_type": "demo",  # Use demo mode
                "connection_params": {},
                "table_or_collection": "test_table",
                "columns_or_fields": ["title", "content"],
                "text_fields": ["title", "content"]
            }
            
            response = await client.post(
                "http://localhost:8000/ingest-data-async",
                json=test_config
            )
            
            if response.status_code == 200:
                result = response.json()
                batch_id = result.get("batch_id")
                print(f"✅ Async ingestion endpoint works, batch_id: {batch_id}")
                
                # Test status endpoint
                if batch_id:
                    time.sleep(2)  # Wait a bit
                    status_response = await client.get(f"http://localhost:8000/ingest-status/{batch_id}")
                    if status_response.status_code == 200:
                        print("✅ Status endpoint works")
                    else:
                        print(f"❌ Status endpoint failed: {status_response.status_code}")
                        
            elif response.status_code == 503:
                print("⚠️  Async ingestion not available (Kafka not running)")
            else:
                print(f"❌ Async ingestion endpoint failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False
    
    print("\n🎉 All tests completed!")
    return True

async def test_demo_mode():
    """Test the demo mode functionality."""
    print("\n🎭 Testing Demo Mode...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test synchronous ingestion with demo mode
            demo_config = {
                "db_type": "demo",
                "connection_params": {},
                "table_or_collection": "articles",
                "columns_or_fields": ["title", "content", "author"],
                "text_fields": ["title", "content"]
            }
            
            print("Starting demo data ingestion...")
            response = await client.post(
                "http://localhost:8000/ingest-data",
                json=demo_config
            )
            
            if response.status_code == 200:
                print("✅ Demo data ingestion started")
                
                # Wait for ingestion to complete
                time.sleep(5)
                
                # Test chat functionality
                chat_request = {
                    "message": "What articles do you have about technology?",
                    "user_name": "test_user"
                }
                
                chat_response = await client.post(
                    "http://localhost:8000/chat",
                    json=chat_request
                )
                
                if chat_response.status_code == 200:
                    result = chat_response.json()
                    print("✅ Chat functionality works")
                    print(f"Response: {result.get('response', 'No response')[:100]}...")
                else:
                    print(f"❌ Chat failed: {chat_response.status_code}")
                    
            else:
                print(f"❌ Demo data ingestion failed: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Demo mode test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting integration tests...")
    
    async def run_all_tests():
        print("Testing basic functionality first...")
        if not await test_demo_mode():
            print("❌ Basic functionality test failed")
            return
        
        print("\nTesting Kafka integration...")
        if not await test_kafka_integration():
            print("❌ Kafka integration test failed")
            return
            
        print("\n🎉 All tests passed successfully!")
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
