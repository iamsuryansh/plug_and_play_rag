# 📁 Project Structure

```
plug-and-play-rag/
├── 📄 README.md                    # Main project documentation
├── 🚀 QUICK_START_GUIDE.md        # 2-minute setup guide
├── ✅ GETTING_STARTED_CHECKLIST.md # Step-by-step verification
├── 🗺️ DOCUMENTATION_GUIDE.md      # Navigation guide
├── 🐳 README.docker.md            # Docker deployment guide
├── 🔧 LLM_CONFIGURATION.md        # AI provider setup
│
├── ⚙️ Core Configuration
│   ├── config/app_config.yaml     # Main configuration file
│   ├── .env.template              # Environment variables template
│   ├── docker-compose.yml         # Docker orchestration
│   └── Dockerfile                 # Container definition
│
├── 🚀 Quick Start Scripts
│   ├── setup.py                   # Interactive setup wizard (Docker)
│   ├── setup_venv.py              # Virtual environment setup
│   ├── deploy.sh                  # One-command Docker deployment
│   ├── dev.sh                     # Development server (venv)
│   ├── run.py                     # Development server runner
│   └── docker_main.py             # Docker entry point
│
├── 📊 Application Code
│   └── app/                       # Main application
│       ├── main.py                # FastAPI application
│       ├── config/                # Configuration management
│       ├── models/                # Data models
│       ├── api/                   # API endpoints
│       ├── chat/                  # Chat and RAG logic
│       ├── ai/                    # LLM integrations
│       ├── database/              # Data connectors
│       └── embeddings/            # Vector embeddings
│
├── 📁 Data & Storage
│   ├── data/                      # CSV files and data sources
│   ├── chroma_db/                 # Vector database (generated)
│   ├── chat_history/              # Conversation history (generated)
│   └── logs/                      # Application logs (generated)
│
├── 🧪 Testing & Examples
│   ├── tests/                     # Test suite
│   └── examples/                  # Demo scripts and advanced examples
│       ├── demo.py                # Basic usage demo
│       ├── csv_demo.py            # CSV ingestion demo
│       ├── demo_mode.py           # Interactive demo
│       ├── docker-compose-kafka.yml # Kafka integration
│       └── start-with-kafka.sh    # Advanced startup script
│
└── 📚 Documentation
    └── docs/                      # Technical documentation
        ├── CSV_IMPLEMENTATION_SUMMARY.md
        ├── MULTI_LLM_STATUS.md
        ├── PROJECT_STRUCTURE.md
        └── ... (other technical docs)
```

## 🎯 Key Files for Getting Started

| File | Purpose | When to Use |
|------|---------|-------------|
| `README.md` | Project overview & examples | First time visitors |
| `QUICK_START_GUIDE.md` | 2-minute setup | Want to get running fast |
| `setup.py` | Interactive Docker setup | Prefer guided Docker deployment |
| `setup_venv.py` | Virtual environment setup | Local development |
| `dev.sh` | Development server | Local development with venv |
| `config/app_config.yaml` | Main configuration | Customize your system |
| `deploy.sh` | One-command Docker deployment | Deploy to production |
| `docker-compose.yml` | Container orchestration | Docker deployment |

## 🚀 Typical Workflows

### First Time Setup (Docker - Recommended)
1. `QUICK_START_GUIDE.md` → Get overview
2. `python setup.py` → Interactive Docker setup
3. `./deploy.sh` → Deploy system

### Local Development (Virtual Environment)
1. `python3 setup_venv.py` → Set up virtual environment
2. Edit `config/app_config.yaml` → Configure
3. `./dev.sh` → Start development server

### Production Deployment
1. `docker-compose up` → Deploy containers
2. Add data to `data/` folder → Automatic ingestion
3. Access `http://localhost:8000` → Use API

## 🔄 Auto-Generated Folders

These folders are created automatically when you run the system:
- `chroma_db/` - Vector database storage
- `chat_history/` - User conversation history  
- `logs/` - Application logs
- `.venv/` - Python virtual environment (if using setup.py)
