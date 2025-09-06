#!/bin/bash

# 🚀 Development Server Startup Script
# This script activates the virtual environment and starts the development server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Plug-and-Play RAG Development Server${NC}"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${BLUE}Setting up virtual environment...${NC}"
    python3 setup_venv.py
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Unix/Linux/macOS
    source .venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    if [ -f ".env.template" ]; then
        echo -e "${BLUE}📄 Creating .env from template...${NC}"
        cp .env.template .env
        echo -e "${YELLOW}⚠️  Please edit .env file and add your API keys${NC}"
    fi
fi

# Create necessary directories
mkdir -p data logs chroma_db

# Check if data directory has files
if [ -z "$(ls -A data/)" ]; then
    echo -e "${YELLOW}⚠️  No CSV files found in data/ directory${NC}"
    echo -e "${BLUE}📁 Add your CSV files to data/ folder for ingestion${NC}"
fi

# Start the development server
echo -e "${GREEN}🌟 Starting FastAPI development server...${NC}"
echo -e "${BLUE}📍 Server will be available at: http://localhost:8000${NC}"
echo -e "${BLUE}📖 API docs will be available at: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server
python run.py
