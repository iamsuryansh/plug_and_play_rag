#!/usr/bin/env python3
"""
Setup script for Chat with Your Data RAG system.
This script helps users configure their environment.
"""

import os
import shutil
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("🔧 Please edit .env file with your actual configuration:")
        print("   - Add your Gemini API key")
        print("   - Configure database credentials")
        return True
    elif env_file.exists():
        print("ℹ️  .env file already exists")
        return True
    else:
        print("❌ .env.example not found")
        return False

def check_directories():
    """Create necessary directories."""
    directories = ['chroma_db', 'chat_history']
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {dir_name}")

def validate_config():
    """Validate basic configuration."""
    from app.config import settings
    
    issues = []
    
    if not settings.GEMINI_API_KEY:
        issues.append("❌ GEMINI_API_KEY is not set")
    
    print("\n🔍 Configuration validation:")
    if issues:
        for issue in issues:
            print(f"  {issue}")
        print("\n🔧 Please update your .env file with the missing configuration")
        return False
    else:
        print("  ✅ Basic configuration looks good")
        return True

def main():
    """Main setup function."""
    print("🚀 Setting up Chat with Your Data RAG System")
    print("=" * 50)
    
    # Create .env file
    if not create_env_file():
        return
    
    # Create directories
    check_directories()
    
    # Validate configuration
    try:
        config_valid = validate_config()
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("🔧 Please check your .env file")
        config_valid = False
    
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your actual database and API credentials")
    if not config_valid:
        print("2. Run this setup script again to validate configuration")
        print("3. Start the server with: python run.py")
    else:
        print("2. Start the server with: python run.py")
        print("3. Visit http://localhost:8000/docs for API documentation")
        print("4. Use the /ingest-data endpoint to load your data")
        print("5. Start chatting with your data!")
    
    print("\n📖 For more information, see README.md")

if __name__ == "__main__":
    main()
