# LLM Configuration Guide - Plug-and-Play RAG

This guide shows how to configure different LLM providers for the Plug-and-Play RAG system.

## Gemini AI (Default)

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

## Ollama (Local LLM)

First, install and start Ollama:
```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (e.g., llama2)
ollama pull llama2

# Start Ollama server (usually runs on localhost:11434)
ollama serve
```

Then configure:
```bash
LLM_PROVIDER=ollama
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama2
```

Popular Ollama models:
- `llama2` - General purpose chat model
- `codellama` - Code-focused model  
- `mistral` - Fast and efficient model
- `neural-chat` - Conversational model
- `llama2:13b` - Larger version for better quality

## LM Studio (Local LLM with GUI)

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., TheBloke/Llama-2-7B-Chat-GGML)
3. Start the local server (usually localhost:1234)

Configure:
```bash
LLM_PROVIDER=lmstudio
LMSTUDIO_ENDPOINT=http://localhost:1234
LMSTUDIO_MODEL=local-model
```

## OpenAI-Compatible APIs

For services that implement OpenAI's chat completions API:

### Together AI
```bash
LLM_PROVIDER=openai-compatible
LLM_ENDPOINT_URL=https://api.together.xyz/v1/chat/completions
LLM_API_KEY=your_together_api_key
LLM_MODEL_NAME=NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO
```

### Anyscale
```bash
LLM_PROVIDER=openai-compatible
LLM_ENDPOINT_URL=https://api.endpoints.anyscale.com/v1/chat/completions
LLM_API_KEY=your_anyscale_api_key
LLM_MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
```

### Local vLLM Server
```bash
LLM_PROVIDER=openai-compatible
LLM_ENDPOINT_URL=http://localhost:8000/v1/chat/completions
LLM_MODEL_NAME=your_model_name
```

## Custom API Endpoints

For completely custom APIs with different request/response formats:

```bash
LLM_PROVIDER=custom
LLM_ENDPOINT_URL=https://your-custom-api.com/generate
LLM_API_KEY=your_api_key
LLM_MODEL_NAME=your_model_name
```

You can also configure custom request templates and headers programmatically when creating the client.

## Runtime Provider Switching

You can switch LLM providers at runtime using the API:

```bash
# Check current provider
curl http://localhost:8001/api/llm/current

# Get supported providers
curl http://localhost:8001/api/llm/providers

# Switch to Ollama
curl -X POST http://localhost:8001/api/llm/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama", "model_name": "llama2"}'

# Switch to custom endpoint
curl -X POST http://localhost:8001/api/llm/switch \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "custom",
    "model_name": "my-model",
    "endpoint_url": "http://localhost:8080/chat",
    "api_key": "optional-key"
  }'
```

## Performance Considerations

- **Gemini**: Cloud-based, good quality, requires API key
- **Ollama**: Local, private, requires GPU for good performance
- **LM Studio**: Local with GUI, good for experimentation
- **Custom APIs**: Varies based on provider and hosting

For production use:
- Gemini for cloud deployment with good performance
- Ollama with GPU for on-premise deployment
- Custom endpoints for enterprise integrations
