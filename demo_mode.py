#!/usr/bin/env python3
"""
Demo mode for Chat with Your Data - loads sample data directly into embeddings
without requiring a database setup.
"""

import asyncio
import json
from pathlib import Path
from app.embeddings.manager import EmbeddingManager
from app.config import settings

async def load_demo_data():
    """Load demo data directly into the vector database."""
    
    # Check if sample data exists
    sample_file = Path('sample_articles.json')
    if not sample_file.exists():
        print("❌ Sample data not found. Run 'python generate_demo_data.py' first.")
        return False
    
    try:
        # Load sample data
        with open(sample_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        print(f"📄 Loaded {len(articles)} sample articles")
        
        # Initialize embedding manager
        print("🔧 Initializing embedding manager...")
        embedding_manager = EmbeddingManager()
        await embedding_manager.initialize()
        
        # Add documents to vector database
        print("🧠 Creating embeddings and storing in vector database...")
        text_fields = ["title", "content", "category", "author"]
        
        num_added = await embedding_manager.add_documents(articles, text_fields)
        print(f"✅ Added {num_added} documents to vector database")
        
        # Get collection stats
        stats = embedding_manager.get_collection_stats()
        print(f"📊 Vector database stats: {stats}")
        
        # Cleanup
        await embedding_manager.cleanup()
        
        print("\n🎉 Demo data loaded successfully!")
        print("You can now start the server and chat with your data:")
        print("   python run.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading demo data: {e}")
        return False

async def test_search():
    """Test search functionality with demo data."""
    try:
        # Initialize embedding manager
        embedding_manager = EmbeddingManager()
        await embedding_manager.initialize()
        
        # Test search
        print("\n🔍 Testing search functionality:")
        test_query = "machine learning and artificial intelligence"
        results = await embedding_manager.search_similar(test_query, n_results=3)
        
        print(f"Query: '{test_query}'")
        print(f"Found {len(results)} similar documents:")
        
        for i, doc in enumerate(results, 1):
            metadata = doc.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            distance = doc.get('distance', 'N/A')
            print(f"  {i}. {title} (similarity: {1-distance:.3f})")
        
        await embedding_manager.cleanup()
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")

def main():
    """Main function for demo mode."""
    print("🚀 Chat with Your Data - Demo Mode")
    print("=" * 40)
    print("This will load sample data directly into the vector database")
    print("without requiring PostgreSQL or MongoDB setup.")
    print()
    
    # Run async functions
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(load_demo_data())
        if success:
            loop.run_until_complete(test_search())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
