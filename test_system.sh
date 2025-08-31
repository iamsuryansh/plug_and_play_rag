#!/bin/bash

# Plug-and-Play RAG System Test Script
# ====================================
# Comprehensive testing of all system components

echo "🔌 Plug-and-Play RAG - System Testing"n/bash

# Test script for LLM provider functionality

echo "=== Plug-and-Play RAG - LLM Provider Testing ==="
echo

echo "1. Current LLM Provider:"
curl -s http://localhost:8001/api/llm/current | python3 -m json.tool
echo

echo "2. Available Providers:"
curl -s http://localhost:8001/api/llm/providers | python3 -c "
import sys
import json
data = json.load(sys.stdin)
for provider, info in data.items():
    print(f'- {provider}: {info[\"description\"]}')
    if 'default_endpoint' in info:
        print(f'  Default endpoint: {info[\"default_endpoint\"]}')
    if 'default_models' in info:
        print(f'  Default models: {info[\"default_models\"]}')
    print()
"

echo "3. Health Check:"
curl -s http://localhost:8001/health | python3 -m json.tool
echo

echo "=== Example: Switch to Ollama (if available) ==="
echo "To switch to Ollama, you would run:"
echo 'curl -X POST http://localhost:8001/api/llm/switch \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d {"provider": "ollama", "model_name": "llama2"}'
echo

echo "=== Example: Switch to Custom LLM ==="
echo "To switch to a custom endpoint, you would run:"
echo 'curl -X POST http://localhost:8001/api/llm/switch \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d {"provider": "custom", "model_name": "my-model", "endpoint_url": "http://localhost:8080/chat"}'
echo

echo "=== Example: Test with Demo Script ==="
echo "You can also use the comprehensive demo script:"
echo 'python demo.py full                    # Run complete demo'
echo 'python demo.py health                  # Quick health check'
echo 'python demo.py providers               # List LLM providers'
echo 'python demo.py chat "your question"    # Test chat'
echo
echo "=== Integration Test (Advanced) ==="
echo "For Kafka/Redis testing:"
echo 'python test_integration.py'
