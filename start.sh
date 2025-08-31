#!/bin/bash

# Plug-and-Play RAG - Startup Script
# This script starts the complete RAG system with optional Kafka integration

set -e

echo "� Starting Plug-and-Play RAG System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is required but not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is required but not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies are available${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOL
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/dbname
MONGODB_URL=mongodb://localhost:27017/

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis Configuration  
REDIS_URL=redis://localhost:6379

# Worker Configuration
INGESTION_WORKERS=2
EMBEDDING_WORKERS=3
EOL
    echo -e "${YELLOW}⚠️  Please update the .env file with your configuration${NC}"
fi

# Start infrastructure services
echo -e "${BLUE}Starting infrastructure services (Kafka, Redis)...${NC}"
docker-compose up -d zookeeper kafka redis

echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Infrastructure services failed to start${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}✅ Infrastructure services are running${NC}"

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Start the application
echo -e "${BLUE}Starting the FastAPI application...${NC}"
echo -e "${YELLOW}The API will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}API documentation will be available at: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Kafka UI will be available at: http://localhost:8080${NC}"

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start the FastAPI application in the background
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Start workers in the background
python run_workers.py &
WORKERS_PID=$!

echo -e "${GREEN}🎉 System started successfully!${NC}"
echo -e "${BLUE}Services running:${NC}"
echo -e "  • FastAPI API: http://localhost:8000"
echo -e "  • API Docs: http://localhost:8000/docs"  
echo -e "  • Kafka UI: http://localhost:8080"
echo -e "  • Redis: localhost:6379"
echo -e "  • Kafka: localhost:9092"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for processes
wait $API_PID $WORKERS_PID
