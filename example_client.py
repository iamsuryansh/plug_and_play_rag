#!/usr/bin/env python3
"""
Example client to demonstrate how to use the Chat with Your Data API.
"""

import requests
import json
import time

class ChatClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def health_check(self):
        """Check if the API is running."""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API is running!")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to API. Make sure the server is running.")
            return False
    
    def ingest_sample_data(self):
        """Ingest sample data (you need to modify this for your database)."""
        # Example for PostgreSQL
        config = {
            "db_type": "postgresql",
            "connection_params": {
                "host": "localhost",
                "port": 5432,
                "user": "your_username",
                "password": "your_password",
                "database": "your_database"
            },
            "table_or_collection": "your_table",
            "columns_or_fields": ["id", "title", "content"],
            "text_fields": ["title", "content"]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ingest-data",
                json=config
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Data ingestion started: {result['message']}")
                return True
            else:
                print(f"❌ Data ingestion failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error during data ingestion: {e}")
            return False
    
    def chat(self, user_name: str, message: str):
        """Send a chat message."""
        chat_request = {
            "user_name": user_name,
            "message": message,
            "max_results": 5,
            "include_history": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json=chat_request
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🤖 Assistant: {result['response']}")
                
                if result.get('sources'):
                    print("\n📚 Sources:")
                    for i, source in enumerate(result['sources'], 1):
                        metadata = source.get('metadata', {})
                        print(f"  {i}. {metadata}")
                return True
            else:
                print(f"❌ Chat failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during chat: {e}")
            return False
    
    def chat_stream(self, user_name: str, message: str):
        """Send a chat message with streaming response."""
        chat_request = {
            "user_name": user_name,
            "message": message,
            "max_results": 5,
            "include_history": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/stream",
                json=chat_request,
                stream=True
            )
            
            if response.status_code == 200:
                print("\n🤖 Assistant (streaming): ", end="", flush=True)
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            if data.strip() == '[DONE]':
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if chunk.get('type') == 'content':
                                    print(chunk.get('content', ''), end="", flush=True)
                                elif chunk.get('type') == 'sources':
                                    sources = chunk.get('sources', [])
                                    if sources:
                                        print(f"\n\n📚 Found {len(sources)} relevant sources")
                                        print("🤖 Assistant (streaming): ", end="", flush=True)
                            except json.JSONDecodeError:
                                continue
                
                print()  # New line after streaming
                return True
            else:
                print(f"❌ Streaming chat failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during streaming chat: {e}")
            return False
    
    def get_history(self, user_name: str):
        """Get chat history for a user."""
        try:
            response = requests.get(f"{self.base_url}/chat/history/{user_name}")
            if response.status_code == 200:
                result = response.json()
                history = result.get('history', [])
                print(f"\n📜 Chat History for {user_name} ({len(history)} messages):")
                for msg in history:
                    role = msg['role'].upper()
                    content = msg['content']
                    timestamp = msg['timestamp']
                    print(f"  [{timestamp}] {role}: {content}")
                return True
            else:
                print(f"❌ Failed to get history: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error getting history: {e}")
            return False

def main():
    """Main function to demonstrate the client."""
    print("🚀 Chat with Your Data - Example Client")
    print("=" * 40)
    
    client = ChatClient()
    
    # Check if API is running
    if not client.health_check():
        return
    
    print("\nThis is a demo client for the Chat with Your Data API.")
    print("Make sure you have:")
    print("1. Updated your .env file with database credentials and Gemini API key")
    print("2. Ingested some data using the /ingest-data endpoint")
    print("3. Started the server with 'python run.py'")
    
    user_name = input("\nEnter your username: ").strip()
    if not user_name:
        user_name = "demo_user"
    
    print(f"\nWelcome {user_name}! You can now chat with your data.")
    print("Type 'quit' to exit, 'history' to see chat history, or 'help' for commands.")
    
    while True:
        try:
            message = input(f"\n{user_name}: ").strip()
            
            if not message:
                continue
            
            if message.lower() == 'quit':
                print("👋 Goodbye!")
                break
            elif message.lower() == 'history':
                client.get_history(user_name)
                continue
            elif message.lower() == 'help':
                print("\nAvailable commands:")
                print("  quit     - Exit the chat")
                print("  history  - Show chat history")
                print("  help     - Show this help message")
                print("  Or just type any question about your data!")
                continue
            
            # Use streaming chat for better experience
            client.chat_stream(user_name, message)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
