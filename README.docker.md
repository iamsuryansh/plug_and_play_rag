# � Docker Deployment Guide

**Deploy your Plug-and-Play RAG system anywhere with Docker!**

This guide shows you how to deploy the RAG system using Docker containers. Perfect for production environments, cloud deployment, or when you want consistent behavior across different machines.

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Clone and navigate
git clone <your-repo-url>
cd plug-and-play-rag

# 2. Quick setup with our automated script
python setup.py

# 3. Deploy with Docker
./deploy.sh
```

**🎉 Done!** Your RAG system is running at `http://localhost:8000`

---

## 🎯 Why Use Docker?

| Benefit | Description |
|---------|-------------|
| **🔒 Consistent Environment** | Works the same on your laptop, server, or cloud |
| **📦 All Dependencies Included** | No need to install Python, databases, or other tools |
| **🚀 Easy Scaling** | Scale up to handle more users and data |
| **🔄 Simple Updates** | Update with a single command |
| **🛡️ Isolation** | Won't interfere with other applications |

---

## 📋 Prerequisites

Make sure you have installed:
- **Docker** (version 20.0+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (usually included with Docker)

### Quick Docker Installation
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# macOS (with Homebrew)
brew install docker

# Windows
# Download Docker Desktop from https://docker.com
```

---

```yaml
llm:
  provider: "gemini"
  api_key: "${GEMINI_API_KEY}"
  model_name: "gemini-pro"
  temperature: 0.7
```

#### OpenAI

```yaml
llm:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
  model_name: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 1000
```

#### Ollama (Local)

```yaml
llm:
  provider: "ollama"
  api_url: "http://localhost:11434"
  model_name: "llama2"
  temperature: 0.7
```

#### Custom LLM Server

```yaml
llm:
  provider: "custom"
  api_url: "http://your-server.com/api/v1"
  api_key: "${CUSTOM_API_KEY}"
  model_name: "your-model"
  custom_headers:
    Authorization: "Bearer ${API_KEY}"
  request_format:
    messages: true
    stream: true
```

### CSV Data Source Configuration

```yaml
csv_sources:
  - name: "knowledge_base"
    file_path: "knowledge.csv"  # Relative to data/ directory
    delimiter: ","
    has_header: true
    encoding: "utf-8"
    columns:
      - name: "title"
        type: "text"
        required: true
      - name: "content"
        type: "text"  
        required: true
      - name: "category"
        type: "text"
        required: false
      - name: "score"
        type: "float"
        required: false
    text_columns: ["title", "content"]
    metadata_columns: ["category", "score"]
    chunk_size: 1000
```

### Database Configuration

```yaml
databases:
  my_postgres:
    type: "postgresql"
    host: "${DB_HOST}"
    port: 5432
    database: "${DB_NAME}"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"

database_sources:
  - name: "articles"
    database_config: "my_postgres"
    table_or_collection: "articles"
    columns_or_fields: ["title", "content", "category"]
    text_fields: ["title", "content"]
    query_filter:
      status: "published"
```

## 🐳 Docker Deployment

### Single Container Deployment

```bash
# Build the image
docker build -t plug-and-play-rag .

# Run with mounted configuration
docker run -d \\
  --name rag-system \\
  -p 8000:8000 \\
  -v $(pwd)/config:/app/config:ro \\
  -v $(pwd)/data:/app/data:ro \\
  -v $(pwd)/logs:/app/logs \\
  -e GEMINI_API_KEY=your_api_key \\
  plug-and-play-rag
```

### Docker Compose Deployment

```bash
# Basic deployment
docker-compose -f docker-compose.plug-and-play.yml up -d

# With databases
docker-compose -f docker-compose.plug-and-play.yml --profile with-db up -d

# View logs
docker-compose logs -f plug-and-play-rag
```

## 📊 API Endpoints

### Chat Endpoints

- `POST /chat` - Standard chat with JSON response
- `POST /chat/stream` - Streaming chat responses
- `GET /health` - Health check endpoint

### Data Management

- `POST /ingest-csv` - Manually ingest CSV data
- `GET /config/info` - View current configuration

### Example Chat Request

```json
{
  "message": "What is artificial intelligence?",
  "user_name": "user123",
  "max_results": 5,
  "include_history": true
}
```

### Example Response

```json
{
  "user_name": "user123",
  "response": "Artificial intelligence (AI) refers to...",
  "sources": [
    {
      "content": "AI is a branch of computer science...",
      "metadata": {
        "source": "csv",
        "category": "technology",
        "title": "Introduction to AI"
      }
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔧 Environment Variables

Key environment variables you can set:

```bash
# Required
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Database (if using)
DB_HOST=localhost
DB_USER=username
DB_PASSWORD=password

# Optional
CONFIG_PATH=/app/config/app_config.yaml
LOG_LEVEL=info
```

## 📁 Directory Structure

```
/app/
├── config/
│   └── app_config.yaml    # Main configuration
├── data/
│   ├── sample_data.csv    # CSV data files
│   └── your_data.csv
├── logs/                  # Application logs
├── chroma_db/            # Vector database storage
└── docker_main.py        # Docker entry point
```

## 🚀 Production Deployment

### Using Docker Swarm

```yaml
version: '3.8'
services:
  rag-system:
    image: plug-and-play-rag:latest
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    volumes:
      - config:/app/config:ro
      - data:/app/data:ro
    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_key
    secrets:
      - gemini_key
```

### Using Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plug-and-play-rag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: plug-and-play-rag
  template:
    spec:
      containers:
      - name: rag-system
        image: plug-and-play-rag:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: data
          mountPath: /app/data
          readOnly: true
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: gemini-api-key
```

## 🔍 Monitoring and Logging

### Health Checks

The system includes comprehensive health checks:

- Container health: `curl http://localhost:8000/health`
- Service dependencies: Database connections, vector DB, LLM connectivity
- Data ingestion status: Track ingestion progress

### Logging

Logs are written to:
- Console: Real-time application logs
- File: `/app/logs/app.log` for persistence
- Structured logging with timestamps and log levels

### Monitoring Integration

```yaml
# Add to docker-compose for monitoring
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🛠️ Troubleshooting

### Common Issues

1. **Configuration not found**
   ```bash
   # Check if config file exists
   ls -la config/app_config.yaml
   
   # Verify YAML syntax
   docker run --rm -v $(pwd)/config:/config mikefarah/yq eval 'keys' /config/app_config.yaml
   ```

2. **Data files missing**
   ```bash
   # Check data directory
   ls -la data/
   
   # Verify file permissions
   chmod 644 data/*.csv
   ```

3. **API key issues**
   ```bash
   # Check environment variables
   docker exec plug-and-play-rag env | grep API_KEY
   ```

4. **Database connection issues**
   ```bash
   # Test database connectivity
   docker exec plug-and-play-rag curl -f http://localhost:8000/health
   ```

### Debug Mode

Enable debug logging:

```yaml
# In config/app_config.yaml
server:
  log_level: "debug"
```

Or via environment:

```bash
docker run -e LOG_LEVEL=debug plug-and-play-rag
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, ChromaDB, and sentence-transformers
- Supports multiple LLM providers for flexibility
- Designed for production deployment with Docker and Kubernetes

---

**Ready to deploy your RAG system anywhere! 🚀**
