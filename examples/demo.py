#!/usr/bin/env python3
"""
Plug-and-Play RAG - Demo and Usage Examples
============================================

This file contains examples and demo functionality for the Plug-and-Play RAG system.
Run different functions to test various features of the system.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"

class PlugAndPlayRAGDemo:
    """Demo class for Plug-and-Play RAG functionality."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def health_check(self):
        """Check system health."""
        print("🔍 Checking system health...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"📝 Message: {data['message']}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def list_llm_providers(self):
        """List available LLM providers."""
        print("\n🤖 Available LLM Providers:")
        try:
            response = await self.client.get(f"{self.base_url}/api/llm/providers")
            providers = response.json()
            
            for name, info in providers.items():
                print(f"\n📋 {name.upper()}:")
                print(f"   Description: {info['description']}")
                print(f"   Requires API Key: {info['requires_api_key']}")
                print(f"   Requires Endpoint: {info['requires_endpoint']}")
                
                if 'default_endpoint' in info:
                    print(f"   Default Endpoint: {info['default_endpoint']}")
                if 'default_models' in info:
                    print(f"   Default Models: {', '.join(info['default_models'])}")
                    
        except Exception as e:
            print(f"❌ Failed to list providers: {e}")
    
    async def get_current_llm(self):
        """Get current LLM provider."""
        print("\n🎯 Current LLM Provider:")
        try:
            response = await self.client.get(f"{self.base_url}/api/llm/current")
            data = response.json()
            print(f"   Provider: {data['provider']}")
            print(f"   Model: {data['model']}")
            print(f"   Status: {data['status']}")
        except Exception as e:
            print(f"❌ Failed to get current LLM: {e}")
    
    async def demo_data_ingestion(self):
        """Demo data ingestion with sample data."""
        print("\n📥 Demo Data Ingestion:")
        
        # Sample data for ingestion
        demo_config = {
            "db_type": "demo",
            "table_or_collection": "articles",
            "text_fields": ["title", "content"]
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/ingest-data",
                json=demo_config
            )
            
            if response.status_code == 200:
                print("✅ Demo data ingestion started successfully")
                data = response.json()
                print(f"📊 Batch ID: {data.get('batch_id', 'N/A')}")
            else:
                print(f"❌ Ingestion failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Demo ingestion failed: {e}")
    
    async def demo_chat(self, message: str = "What data do you have available?", user_name: str = "demo"):
        """Demo chat functionality."""
        print(f"\n💬 Demo Chat (User: {user_name}):")
        print(f"🗨️  Question: {message}")
        
        chat_request = {
            "message": message,
            "user_name": user_name
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat",
                json=chat_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data['response']}")
                
                if 'sources' in data and data['sources']:
                    print("\n📚 Sources:")
                    for source in data['sources'][:3]:  # Show top 3 sources
                        print(f"   - {source.get('content', 'Unknown')[:100]}...")
            else:
                print(f"❌ Chat failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Demo chat failed: {e}")
    
    async def switch_llm_demo(self, provider: str = "ollama", model_name: str = "llama2"):
        """Demo LLM provider switching."""
        print(f"\n🔄 Demo LLM Switching to {provider}:")
        
        switch_request = {
            "provider": provider,
            "model_name": model_name
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/llm/switch",
                json=switch_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully switched to {data['provider']}")
                print(f"🎯 Model: {data['model']}")
                print(f"🧪 Test Response: {data['test_response'][:100]}...")
            else:
                error_data = response.json()
                print(f"❌ Switch failed: {error_data.get('detail', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ LLM switch demo failed: {e}")
    
    async def run_full_demo(self):
        """Run complete demo sequence."""
        print("🔌 Starting Plug-and-Play RAG Full Demo")
        print("=" * 50)
        
        # Health check
        if not await self.health_check():
            print("❌ System not healthy, stopping demo")
            return
        
        # List providers
        await self.list_llm_providers()
        
        # Show current LLM
        await self.get_current_llm()
        
        # Demo data ingestion
        await self.demo_data_ingestion()
        
        # Wait a bit for ingestion
        print("\n⏳ Waiting 3 seconds for data processing...")
        await asyncio.sleep(3)
        
        # Demo chat
        await self.demo_chat()
        
        # Demo different questions
        await self.demo_chat("Tell me about AI and machine learning", "researcher")
        await self.demo_chat("What are the most recent articles?", "analyst")
        
        print("\n✅ Demo completed successfully!")
        print("🎯 Try the API documentation at: http://localhost:8001/docs")
        print("🔌 Plug-and-Play RAG is ready for your data!")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Standalone demo functions
async def quick_health_check():
    """Quick health check function."""
    demo = PlugAndPlayRAGDemo()
    await demo.health_check()
    await demo.close()

async def quick_providers_list():
    """Quick providers list function."""
    demo = PlugAndPlayRAGDemo()
    await demo.list_llm_providers()
    await demo.close()

async def quick_chat_demo():
    """Quick chat demo function."""
    demo = PlugAndPlayRAGDemo()
    await demo.demo_chat("Hello! What can you help me with?")
    await demo.close()

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "health":
            asyncio.run(quick_health_check())
        elif command == "providers":
            asyncio.run(quick_providers_list())
        elif command == "chat":
            message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello!"
            demo = PlugAndPlayRAGDemo()
            asyncio.run(demo.demo_chat(message))
            asyncio.run(demo.close())
        elif command == "full":
            demo = PlugAndPlayRAGDemo()
            asyncio.run(demo.run_full_demo())
            asyncio.run(demo.close())
        else:
            print("Usage:")
            print("  python demo.py health      - Check system health")
            print("  python demo.py providers   - List LLM providers")
            print("  python demo.py chat [msg]  - Test chat functionality")
            print("  python demo.py full        - Run complete demo")
    else:
        # Run full demo by default
        demo = PlugAndPlayRAGDemo()
        asyncio.run(demo.run_full_demo())
        asyncio.run(demo.close())
