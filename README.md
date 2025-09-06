# 🚀 Plug-and-Play RAG System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-orange.svg)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Multi-LLM](https://img.shields.io/badge/Multi--LLM-Supported-purple.svg)](#-supported-llm-providers)

> **🎯 Chat with your data using AI - No coding required!**

Transform your CSV files, databases, and documents into an intelligent AI assistant that understands and answers questions about your data in natural language.

---

## 🌟 What Can You Do?

**Instead of complex queries like:**
```sql
SELECT * FROM sales WHERE region='North' AND revenue > 10000 AND date > '2024-01-01'
```

**Just ask:**
> *"Show me high-revenue sales from the North region this year"*

**Instead of searching through documents manually:**
**Just ask:**
> *"What are the key findings from our customer feedback?"*

---

## ⚡ Quick Start (2 Minutes Setup)

### Option 1: Automated Setup (Recommended)
```bash
# 1. Clone the repository
git clone https://github.com/your-username/plug-and-play-rag.git
cd plug-and-play-rag

# 2. Run interactive setup
python setup.py

# 3. Deploy with one command
./deploy.sh
```

### Option 2: Local Development (Virtual Environment)
```bash
# 1. Set up virtual environment and dependencies
python3 setup_venv.py

# 2. Add your CSV files to data folder
cp your-data.csv data/

# 3. Configure your API keys
cp .env.template .env
# Edit .env with your API keys

# 4. Start development server
./dev.sh
```

### Option 3: Manual Docker Setup
```bash
# 1. Copy your CSV files to data folder
cp your-data.csv data/

# 2. Configure your settings
cp config/app_config.yaml config/my_config.yaml
# Edit my_config.yaml with your preferences

# 3. Start the system
docker-compose up
```

### 🎉 That's it! Your AI assistant is ready at `http://localhost:8000`

---

## 💡 Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **🔧 Zero-Code Setup** | Configure everything through YAML files | No programming required |
| **🐳 Docker Ready** | One-command deployment | Works everywhere |
| **🤖 Multi-LLM Support** | Gemini, OpenAI, Ollama, LM Studio | Choose your preferred AI |
| **📊 Any Data Source** | CSV, PostgreSQL, MongoDB | Use your existing data |
| **🌊 Real-time Chat** | Streaming responses | Fast, interactive experience |
| **📝 Smart Memory** | Remembers conversation history | Contextual conversations |
| **🔍 Smart Search** | Finds relevant information automatically | Accurate, sourced answers |

---

## 🗂️ Supported Data Sources

- **📄 CSV Files** - Perfect for spreadsheets and exported data
- **🐘 PostgreSQL** - Enterprise relational databases  
- **🍃 MongoDB** - Document and NoSQL databases
- **🔜 More coming soon** - MySQL, SQLite, APIs, and more

## 🤖 Supported LLM Providers

- **🔮 Google Gemini** - Powerful and fast (recommended)
- **🧠 OpenAI GPT** - Most popular choice
- **🦙 Ollama** - Run locally on your machine
- **💻 LM Studio** - Local models with GPU acceleration  
- **🔗 Custom APIs** - Bring your own LLM endpoint

---

## 📚 Step-by-Step Guide

### 1. 🎯 Set Your Goal
What do you want to ask your data? Examples:
- Analyze customer feedback patterns
- Search through technical documentation
- Query sales and revenue data
- Find insights in research papers

### 2. 📁 Prepare Your Data
Put your data in the `data/` folder:
```
data/
├── customer_feedback.csv
├── sales_data.csv
└── product_catalog.csv
```

### 3. ⚙️ Configure Your System
Edit `config/app_config.yaml`:
```yaml
app_name: "My Data Assistant"

# Choose your AI provider
llm:
  provider: "gemini"  # or openai, ollama, lmstudio
  api_key: "${GEMINI_API_KEY}"
  
# Configure your data sources
csv_sources:
  - name: "customer_feedback"
    file_path: "data/customer_feedback.csv"
    text_columns: ["feedback", "comments"]
    metadata_columns: ["date", "rating", "product"]
```

### 4. 🔑 Set Your API Keys
Copy `.env.template` to `.env` and add your API keys:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # if using OpenAI
```

### 5. 🚀 Launch Your Assistant
```bash
# Automated deployment
./deploy.sh

# Or manual Docker deployment
docker-compose -f docker-compose.plug-and-play.yml up
```

### 6. 💬 Start Chatting!
```bash
# Test your assistant
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What patterns do you see in customer feedback?", "user_name": "analyst"}'
```

---

## 🔧 Configuration Examples

### Basic CSV Setup
```yaml
llm:
  provider: "gemini"
  api_key: "${GEMINI_API_KEY}"

csv_sources:
  - name: "products"
    file_path: "data/products.csv"
    text_columns: ["name", "description"]
    metadata_columns: ["category", "price", "id"]

auto_ingest_on_startup: true
```

### PostgreSQL Database Setup
```yaml
llm:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"

database_sources:
  - name: "user_database" 
    db_type: "postgresql"
    connection_params:
      host: "localhost"
      port: 5432
      database: "mydb"
      username: "${DB_USERNAME}"
      password: "${DB_PASSWORD}"
    table_or_collection: "articles"
    text_fields: ["title", "content"]
```

### Local Ollama Setup (No API Keys Needed!)
```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"
  model_name: "llama3"

csv_sources:
  - name: "documents"
    file_path: "data/docs.csv"
    text_columns: ["content"]
```

---

## 🚀 API Reference

### Health Check
```bash
GET /health
# Response: {"status": "healthy", "timestamp": "2024-08-31T10:00:00Z"}
```

### Chat with Your Data
```bash
POST /chat
{
  "message": "What insights can you find in the data?",
  "user_name": "analyst",
  "max_results": 5,
  "include_history": true
}
```

### Streaming Chat (Real-time)
```bash
POST /chat/stream
# Returns server-sent events with real-time responses
```

### Data Ingestion
```bash
POST /ingest-data
{
  "db_type": "csv",
  "table_or_collection": "my_data.csv",
  "text_fields": ["title", "content"]
}
```

---

## 🛠️ Advanced Usage

### Custom Docker Setup
```bash
# Build custom image
docker build -t my-rag-system .

# Run with custom config
docker run -p 8000:8000 -v $(pwd)/config:/app/config my-rag-system
```

### Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Run in development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Data Sources
1. Add CSV files to `data/` folder
2. Update `config/app_config.yaml`
3. Restart the system - data is automatically ingested!

---

## 🆘 Troubleshooting

### Common Issues

**❌ "API key not found"**
- Check your `.env` file has the correct API key
- Make sure the key starts with the right prefix (e.g., `AIza...` for Gemini)

**❌ "Docker container won't start"**
- Run `docker-compose logs` to see error details
- Check if ports 8000 is already in use

**❌ "No data found"**
- Verify your CSV files are in the `data/` folder
- Check the column names in your YAML configuration match your CSV headers

**❌ "Slow responses"**
- Try reducing `max_results` in your chat requests
- Consider using a faster LLM provider like Gemini

### Getting Help

1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Look at example configurations in `config/examples/`
3. Open an issue on GitHub with your configuration and error logs

---

## 📊 Example Use Cases

### Business Intelligence
```yaml
# Analyze sales data
csv_sources:
  - name: "sales"
    file_path: "data/sales_2024.csv"
    text_columns: ["product_name", "customer_feedback"]
    metadata_columns: ["date", "revenue", "region"]
```
**Ask:** *"Which products had the highest customer satisfaction in Q2?"*

### Document Search
```yaml
# Search technical documentation
csv_sources:
  - name: "docs"
    file_path: "data/documentation.csv" 
    text_columns: ["title", "content", "summary"]
    metadata_columns: ["category", "last_updated", "author"]
```
**Ask:** *"How do I configure authentication in the API?"*

### Research Analysis
```yaml
# Analyze research papers
csv_sources:
  - name: "papers"
    file_path: "data/research_papers.csv"
    text_columns: ["abstract", "conclusions", "methodology"]
    metadata_columns: ["authors", "journal", "year", "citations"]
```
**Ask:** *"What are the latest trends in machine learning research?"*

---

## 🚀 What's Next?

- **🔗 API Integrations** - Connect to REST APIs and web services
- **📱 Mobile App** - Chat with your data on mobile devices  
- **🎨 Web UI** - Beautiful web interface for non-technical users
- **📈 Analytics Dashboard** - Visualize your data insights
- **🔐 Enterprise Security** - Advanced authentication and permissions

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Show Your Support

If this project helped you, please give it a ⭐ on GitHub!

---

**Made with ❤️ by the AI community**
