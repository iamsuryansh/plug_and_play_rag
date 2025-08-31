# 🚀 Quick Start Guide - Get Running in 2 Minutes!

**Skip the technical details. Get your AI assistant running now!**

---

## 🎯 What You'll Get

After following this guide, you'll have:
- ✅ An AI assistant that answers questions about your data
- ✅ A web API running at `http://localhost:8000`
- ✅ Real-time chat with streaming responses  
- ✅ Automatic data ingestion from your CSV files

---

## ⚡ Method 1: Automated Setup (Recommended)

**Perfect for beginners - just follow the prompts!**

```bash
# 1. Download the project
git clone https://github.com/your-username/plug-and-play-rag.git
cd plug-and-play-rag

# 2. Run the setup wizard
python setup.py

# 3. Deploy everything
./deploy.sh
```

The setup wizard will:
- ✅ Guide you through configuration
- ✅ Help you add your data files  
- ✅ Set up your AI provider (Gemini, OpenAI, etc.)
- ✅ Validate everything works

**🎉 That's it! Your assistant is ready at http://localhost:8000**

---

## ⚡ Method 2: Manual Setup (5 minutes)

**For those who want more control:**

### Step 1: Get Your Files Ready
```bash
# Clone the project
git clone https://github.com/your-username/plug-and-play-rag.git
cd plug-and-play-rag

# Copy your data files
mkdir -p data
cp your-data.csv data/
```

### Step 2: Configure Your AI Provider

Choose one option:

**Option A: Google Gemini (Recommended - Fast & Free tier)**
```bash
# Get API key from: https://makersuite.google.com/app/apikey
cp .env.template .env
echo "GEMINI_API_KEY=your_key_here" >> .env
```

**Option B: OpenAI GPT**
```bash  
# Get API key from: https://platform.openai.com/api-keys
cp .env.template .env
echo "OPENAI_API_KEY=your_key_here" >> .env
```

**Option C: Local Ollama (No API key needed!)**
```bash
# Install Ollama first: https://ollama.ai
ollama pull llama3
# No API key needed!
```

### Step 3: Configure Your Data
Edit `config/app_config.yaml`:

```yaml
app_name: "My Data Assistant"

# Choose your AI (pick one)
llm:
  provider: "gemini"    # or "openai" or "ollama" 
  api_key: "${GEMINI_API_KEY}"  # or "${OPENAI_API_KEY}" or remove for Ollama
  
# Add your CSV files  
csv_sources:
  - name: "my_data"
    file_path: "data/your-data.csv"  # Update this filename
    text_columns: ["title", "content", "description"]  # Update column names
    metadata_columns: ["date", "category", "id"]       # Update column names

auto_ingest_on_startup: true
```

### Step 4: Launch!
```bash
docker-compose -f docker-compose.plug-and-play.yml up --build
```

**🎉 Your assistant is ready at http://localhost:8000**

---

## 🧪 Test Your Assistant

```bash
# Check it's working
curl http://localhost:8000/health

# Ask your first question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What data do you have?", 
    "user_name": "me"
  }'
```

---

## 🎉 Next Steps

### Try These Example Questions:
- *"What patterns do you see in the data?"*
- *"Summarize the key insights"*
- *"Find records related to [your topic]"*
- *"What happened in [specific time period]?"*

### Add More Data:
1. Copy more CSV files to the `data/` folder
2. Update `config/app_config.yaml` to include them
3. Restart: `docker-compose restart`

### Web Interface (Coming Soon):
Visit `http://localhost:8000/docs` for the API documentation

---

## ❓ Need Help?

### Common Issues:

**"No API key found"**
- Check your `.env` file has the right key name
- Make sure there are no extra spaces or quotes

**"Docker won't start"**  
- Check Docker is installed: `docker --version`
- Make sure port 8000 isn't already used

**"No data found"**
- Check your CSV files are in the `data/` folder
- Verify column names in `app_config.yaml` match your CSV headers

### Get Support:
1. Check the [full documentation](README.md)
2. Look at [example configurations](config/examples/)
3. Open an issue on GitHub

---

**🎯 Goal achieved! You now have an AI assistant that understands your data!**
