# 📁 Examples Directory

This directory contains demo scripts and advanced configuration examples.

## 🧪 Demo Scripts

### Basic Usage Examples
- **`demo.py`** - Basic usage demonstration of the RAG system
- **`csv_demo.py`** - CSV data ingestion examples  
- **`demo_mode.py`** - Interactive demo mode

### Advanced Configuration Examples
- **`docker-compose-kafka.yml`** - Docker setup with Kafka integration
- **`start-with-kafka.sh`** - Startup script for Kafka-enabled deployment

### Testing Scripts
- **`test_llm_providers.sh`** - Test multiple LLM providers
- **`test_system.sh`** - System integration tests

## 🚀 How to Use

### Run Basic Demo
```bash
# Make sure your system is running first
python examples/demo.py
```

### Try CSV Demo  
```bash
# Add CSV files to data/ directory first
python examples/csv_demo.py
```

### Advanced Kafka Setup
```bash
# Use Kafka integration for high-scale deployment
docker-compose -f examples/docker-compose-kafka.yml up
```

## 💡 What These Examples Show

- **API Integration** - How to call the RAG system programmatically
- **Data Ingestion** - Different ways to load and process data
- **Multi-LLM Usage** - Switching between different AI providers
- **Streaming Responses** - Real-time chat interactions
- **Error Handling** - Robust error handling patterns
- **Configuration** - Advanced configuration examples

## 🔗 Related Documentation

- Main README: `../README.md`
- Quick Start: `../QUICK_START_GUIDE.md`
- Docker Guide: `../README.docker.md`
- Configuration: `../config/app_config.yaml`
