#!/bin/bash

# Test script for LLM provider functionality

echo "=== Testing LLM Provider Functionality ==="
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

echo "=== Example: Chat with Current LLM ==="
echo "To test the chat functionality:"
echo 'curl -X POST http://localhost:8001/chat \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d {"message": "Hello! What LLM are you?", "user_id": "test-user"}'
