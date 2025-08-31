# ✅ Getting Started Checklist

**Follow this checklist to get your AI assistant running perfectly!**

---

## 📋 Pre-Setup Checklist

### ✅ System Requirements
- [ ] **Docker installed** - [Get Docker](https://docs.docker.com/get-docker/)
- [ ] **Python 3.12+** - [Download Python](https://python.org/downloads)  
- [ ] **Git installed** - [Get Git](https://git-scm.com/)

### ✅ Account Setup (Choose One)
- [ ] **Google AI Studio account** - [Get Gemini API key](https://makersuite.google.com/app/apikey) (Recommended)
- [ ] **OpenAI account** - [Get OpenAI API key](https://platform.openai.com/api-keys)
- [ ] **Ollama installed locally** - [Install Ollama](https://ollama.ai/) (No API key needed)

---

## 🚀 Setup Checklist

### ✅ Method 1: Automated (Recommended)
- [ ] Clone repository: `git clone <repo-url> && cd plug-and-play-rag`
- [ ] Run setup wizard: `python setup.py`
- [ ] Follow the prompts to configure everything
- [ ] Deploy: `./deploy.sh`
- [ ] Test: Visit `http://localhost:8000/health`

### ✅ Method 2: Manual Setup
- [ ] Clone repository: `git clone <repo-url> && cd plug-and-play-rag`
- [ ] Copy data files to `data/` folder
- [ ] Copy environment file: `cp .env.template .env`
- [ ] Add your API key to `.env` file
- [ ] Edit `config/app_config.yaml` with your settings
- [ ] Deploy: `docker-compose -f docker-compose.plug-and-play.yml up`
- [ ] Test: Visit `http://localhost:8000/health`

---

## ✅ Configuration Checklist

### Data Sources
- [ ] **CSV files added** to `data/` folder
- [ ] **Column names configured** in `config/app_config.yaml`
- [ ] **Text columns** specified (what to search through)
- [ ] **Metadata columns** specified (additional info to show)

### AI Provider  
- [ ] **Provider chosen**: Gemini, OpenAI, or Ollama
- [ ] **API key set** in `.env` file (if needed)
- [ ] **Model name configured** in YAML file
- [ ] **Temperature set** (0.0 = focused, 1.0 = creative)

### Server Settings
- [ ] **Port configured** (default: 8000)
- [ ] **CORS enabled** if using from browser
- [ ] **Auto-ingestion enabled** for automatic data processing

---

## ✅ Testing Checklist

### Basic Tests
- [ ] **Health check works**: `curl http://localhost:8000/health`
- [ ] **API docs accessible**: Visit `http://localhost:8000/docs`
- [ ] **Data ingestion completed**: Check logs for "ingestion completed"

### Chat Tests
```bash
# Test basic chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What data do you have?", "user_name": "test"}'
```

- [ ] **Chat endpoint responds** with JSON
- [ ] **Response includes sources** from your data
- [ ] **No error messages** in response
- [ ] **Streaming works** (if enabled): `POST /chat/stream`

### Advanced Tests
- [ ] **Multiple questions work** with same user
- [ ] **Chat history enabled** (responses reference previous questions)
- [ ] **Different users get separate histories**
- [ ] **Search finds relevant results** from your data

---

## 🐛 Troubleshooting Checklist

### If Health Check Fails
- [ ] Check Docker is running: `docker ps`
- [ ] Check logs: `docker-compose logs`
- [ ] Verify port 8000 is available: `netstat -an | grep 8000`
- [ ] Try different port in configuration

### If Chat Fails
- [ ] Verify API key is correct in `.env` file
- [ ] Check API key has proper format (starts with correct prefix)
- [ ] Confirm data files exist in `data/` folder
- [ ] Review column names in `config/app_config.yaml` match CSV headers
- [ ] Check logs for specific error messages

### If No Data Found
- [ ] Confirm CSV files are in correct location (`data/` folder)
- [ ] Verify file names match configuration
- [ ] Check CSV has headers and data
- [ ] Ensure text columns are not empty
- [ ] Review data ingestion logs

### If Responses Are Poor
- [ ] Try different temperature setting (0.3-0.8)
- [ ] Increase `max_results` in vector_db settings
- [ ] Ensure text columns contain meaningful content
- [ ] Consider using different embedding model
- [ ] Try different LLM provider

---

## ✅ Success Indicators

### You Know It's Working When:
- [ ] ✅ Health check returns `{"status": "healthy"}`
- [ ] ✅ Chat responses include relevant information from your data
- [ ] ✅ Sources are provided with each response
- [ ] ✅ System responds quickly (under 5 seconds)
- [ ] ✅ Chat history works across multiple questions
- [ ] ✅ System handles multiple users simultaneously

### Performance Benchmarks:
- **Health Check**: < 1 second response
- **Data Ingestion**: Completes within 5 minutes for 10k rows
- **Chat Response**: < 5 seconds for typical questions  
- **Streaming**: First chunk arrives within 2 seconds

---

## 🎉 You're Done!

**Congratulations! Your AI assistant is ready to answer questions about your data.**

### Next Steps:
- [ ] Explore the [API documentation](http://localhost:8000/docs)
- [ ] Try different types of questions  
- [ ] Add more data sources
- [ ] Share with your team
- [ ] Consider production deployment

### Need Help?
- 📖 Read the [full documentation](README.md)
- 🐛 Check [troubleshooting guide](README.docker.md#troubleshooting)
- 💬 Open an issue on GitHub
- 📧 Contact support

---

**🚀 Happy chatting with your data!**
