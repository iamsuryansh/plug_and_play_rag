#!/usr/bin/env python3
"""
Setup script for Plug-and-Play RAG system
"""

import os
import sys
import yaml
import shutil
from pathlib import Path


def create_directory_structure():
    """Create required directory structure."""
    directories = [
        "config",
        "data", 
        "logs",
        "chroma_db"
    ]
    
    print("🗂️  Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✓ {directory}/")


def create_sample_config():
    """Create sample configuration file."""
    config_path = Path("config/app_config.yaml")
    
    if config_path.exists():
        response = input("⚠️  Configuration file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   → Skipping configuration file creation")
            return
    
    print("📝 Creating sample configuration file...")
    
    sample_config = {
        "app_name": "Plug-and-Play RAG",
        "version": "1.0.0",
        "description": "Retrieval-Augmented Generation system with multiple data sources",
        
        "llm": {
            "provider": "gemini",
            "api_key": "${GEMINI_API_KEY}",
            "model_name": "gemini-pro",
            "temperature": 0.7
        },
        
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu",
            "batch_size": 32
        },
        
        "vector_db": {
            "type": "chromadb",
            "collection_name": "rag_documents",
            "persist_directory": "/app/chroma_db",
            "similarity_threshold": 0.7,
            "max_results": 10
        },
        
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": False,
            "workers": 1,
            "log_level": "info"
        },
        
        "csv_sources": [
            {
                "name": "sample_articles",
                "file_path": "sample_data.csv",
                "delimiter": ",",
                "has_header": True,
                "encoding": "utf-8",
                "columns": [
                    {
                        "name": "title",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "content", 
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "category",
                        "type": "text",
                        "required": False
                    }
                ],
                "text_columns": ["title", "content"],
                "metadata_columns": ["category"],
                "chunk_size": 1000
            }
        ],
        
        "auto_ingest_on_startup": True,
        "batch_processing": True,
        "enable_chat_history": True,
        "enable_streaming": True,
        "enable_cors": True,
        "cors_origins": ["*"]
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print(f"   ✓ Configuration created: {config_path}")


def copy_sample_data():
    """Copy sample data file to data directory."""
    source = Path("sample_data.csv")
    dest = Path("data/sample_data.csv")
    
    if source.exists():
        print("📊 Copying sample data file...")
        shutil.copy2(source, dest)
        print(f"   ✓ Sample data copied: {dest}")
    else:
        print("⚠️  Sample data file not found, creating placeholder...")
        create_placeholder_csv()


def create_placeholder_csv():
    """Create a placeholder CSV file."""
    csv_content = """title,content,category
"Introduction to AI","Artificial Intelligence is a branch of computer science...","Technology"
"Machine Learning Basics","Machine learning is a subset of AI that focuses on...","Technology"
"Data Science Overview","Data science combines statistical analysis with...","Technology"
"""
    
    with open("data/sample_data.csv", "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    print("   ✓ Placeholder CSV created: data/sample_data.csv")


def create_env_file():
    """Create environment file from template."""
    template_path = Path(".env.template")
    env_path = Path(".env")
    
    if env_path.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   → Skipping .env file creation")
            return
    
    if template_path.exists():
        print("🔐 Creating environment file...")
        shutil.copy2(template_path, env_path)
        print(f"   ✓ Environment file created: {env_path}")
        print("   📝 Please edit .env file with your API keys and configuration")
    else:
        print("⚠️  .env.template not found, creating basic .env file...")
        create_basic_env()


def create_basic_env():
    """Create basic environment file."""
    env_content = """# Plug-and-Play RAG Environment Variables
# Add your API keys and configuration here

# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration (optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ragdb
DB_USER=raguser
DB_PASSWORD=ragpass

# Application Configuration
CONFIG_PATH=/app/config/app_config.yaml
LOG_LEVEL=info
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("   ✓ Basic .env file created")


def check_docker():
    """Check if Docker is available."""
    print("🐳 Checking Docker availability...")
    
    # Check if Docker is installed and running
    docker_available = os.system("docker --version > /dev/null 2>&1") == 0
    docker_running = os.system("docker info > /dev/null 2>&1") == 0
    
    if docker_available:
        print("   ✓ Docker is installed")
        if docker_running:
            print("   ✓ Docker daemon is running")
            return True
        else:
            print("   ❌ Docker daemon is not running")
            print("   → Please start Docker and try again")
            return False
    else:
        print("   ❌ Docker is not installed")
        print("   → Please install Docker: https://docs.docker.com/get-docker/")
        return False


def show_next_steps():
    """Show next steps to the user."""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Edit your API keys in .env file:")
    print("   nano .env")
    
    print("\n2. Customize your configuration (optional):")
    print("   nano config/app_config.yaml")
    
    print("\n3. Add your data files to data/ directory:")
    print("   cp your_data.csv data/")
    
    print("\n4. Run with Docker Compose:")
    print("   docker-compose -f docker-compose.plug-and-play.yml up --build")
    
    print("\n5. Test the API:")
    print("   curl http://localhost:8000/health")
    
    print("\n🔗 Useful commands:")
    print("   # View logs")
    print("   docker-compose logs -f plug-and-play-rag")
    
    print("   # Stop the system")
    print("   docker-compose -f docker-compose.plug-and-play.yml down")
    
    print("   # Run with databases")
    print("   docker-compose -f docker-compose.plug-and-play.yml --profile with-db up")
    
    print("\n📚 Documentation:")
    print("   README.docker.md - Complete setup and usage guide")
    print("   config/app_config.yaml - Configuration reference")
    
    print("\n🚀 Ready to go! Your RAG system will be available at http://localhost:8000")


def main():
    """Main setup function."""
    print("🚀 Plug-and-Play RAG System Setup")
    print("=" * 50)
    
    # Create directory structure
    create_directory_structure()
    
    # Create configuration file
    create_sample_config()
    
    # Copy or create sample data
    copy_sample_data()
    
    # Create environment file
    create_env_file()
    
    # Check Docker
    docker_ok = check_docker()
    
    # Show next steps
    show_next_steps()
    
    if not docker_ok:
        print("\n⚠️  Docker setup required before proceeding with deployment.")
        sys.exit(1)
    
    print(f"\n✨ Setup complete! Happy RAG-ing! ✨")


if __name__ == "__main__":
    main()
