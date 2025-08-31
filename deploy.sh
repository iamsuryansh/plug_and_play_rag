#!/bin/bash

# Plug-and-Play RAG Deployment Script
set -e

echo "🚀 Plug-and-Play RAG Deployment Script"
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if required files exist
check_requirements() {
    print_info "Checking requirements..."
    
    if [ ! -f "docker-compose.plug-and-play.yml" ]; then
        print_error "docker-compose.plug-and-play.yml not found!"
        exit 1
    fi
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found!"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_info "Please edit .env file with your configuration before running again."
            exit 1
        else
            print_error "No .env or .env.template file found!"
            exit 1
        fi
    fi
    
    if [ ! -f "config/app_config.yaml" ]; then
        print_warning "Configuration file not found. Running setup..."
        python3 setup.py
        print_info "Please edit config/app_config.yaml and .env, then run this script again."
        exit 1
    fi
    
    print_status "All requirements satisfied"
}

# Check Docker installation
check_docker() {
    print_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        print_info "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running!"
        print_info "Please start Docker and try again."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        print_info "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_status "Docker is ready"
}

# Load environment variables
load_env() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
        print_status "Environment variables loaded"
    fi
}

# Validate essential configuration
validate_config() {
    print_info "Validating configuration..."
    
    # Check if API key is set (for Gemini by default)
    if [[ -z "$GEMINI_API_KEY" ]] && [[ "$LLM_PROVIDER" != "ollama" ]] && [[ "$LLM_PROVIDER" != "lmstudio" ]]; then
        print_warning "GEMINI_API_KEY is not set in .env file"
        print_info "Make sure to set your LLM provider API key before deployment"
    fi
    
    # Check if data directory exists and has files
    if [ -d "data" ]; then
        file_count=$(find data -name "*.csv" | wc -l)
        if [ $file_count -gt 0 ]; then
            print_status "Found $file_count CSV files in data directory"
        else
            print_warning "No CSV files found in data directory"
            print_info "Add your CSV files to the data/ directory for auto-ingestion"
        fi
    else
        print_warning "data directory not found. Creating..."
        mkdir -p data
        print_info "Add your CSV files to the data/ directory"
    fi
    
    print_status "Configuration validation complete"
}

# Build the Docker image
build_image() {
    print_info "Building Docker image..."
    
    if docker-compose -f docker-compose.plug-and-play.yml build; then
        print_status "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Deploy the application
deploy_app() {
    local profile=""
    
    # Check if user wants to deploy with databases
    read -p "Deploy with database services (PostgreSQL/MongoDB)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        profile="--profile with-db"
        print_info "Deploying with database services..."
    else
        print_info "Deploying application only..."
    fi
    
    print_info "Starting deployment..."
    
    if docker-compose -f docker-compose.plug-and-play.yml $profile up -d; then
        print_status "Deployment started successfully"
    else
        print_error "Deployment failed"
        exit 1
    fi
}

# Wait for health check
wait_for_health() {
    print_info "Waiting for application to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            print_status "Application is healthy and ready!"
            break
        else
            echo -n "."
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Application failed to start within expected time"
        print_info "Check logs with: docker-compose logs plug-and-play-rag"
        exit 1
    fi
}

# Show deployment status
show_status() {
    echo
    echo "🎉 Deployment Complete!"
    echo "====================="
    echo
    
    # Show running containers
    print_info "Running containers:"
    docker-compose -f docker-compose.plug-and-play.yml ps
    
    echo
    print_info "Application URLs:"
    echo "  Health Check: http://localhost:8000/health"
    echo "  Chat API:     http://localhost:8000/chat"
    echo "  API Docs:     http://localhost:8000/docs"
    
    echo
    print_info "Useful commands:"
    echo "  View logs:    docker-compose -f docker-compose.plug-and-play.yml logs -f"
    echo "  Stop system:  docker-compose -f docker-compose.plug-and-play.yml down"
    echo "  Restart:      docker-compose -f docker-compose.plug-and-play.yml restart"
    
    echo
    print_info "Test the API:"
    echo "  curl http://localhost:8000/health"
    echo "  curl -X POST http://localhost:8000/chat \\"
    echo "       -H \"Content-Type: application/json\" \\"
    echo "       -d '{\"message\": \"Hello\", \"user_name\": \"user1\"}'"
    
    echo
    print_status "Your Plug-and-Play RAG system is ready! 🚀"
}

# Handle cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed. Check the logs for details:"
        echo "docker-compose -f docker-compose.plug-and-play.yml logs"
    fi
}

trap cleanup EXIT

# Main execution
main() {
    # Parse command line arguments
    case "${1:-}" in
        "down"|"stop")
            print_info "Stopping Plug-and-Play RAG system..."
            docker-compose -f docker-compose.plug-and-play.yml down
            print_status "System stopped"
            exit 0
            ;;
        "logs")
            docker-compose -f docker-compose.plug-and-play.yml logs -f
            exit 0
            ;;
        "restart")
            print_info "Restarting Plug-and-Play RAG system..."
            docker-compose -f docker-compose.plug-and-play.yml restart
            print_status "System restarted"
            exit 0
            ;;
        "status")
            docker-compose -f docker-compose.plug-and-play.yml ps
            exit 0
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [COMMAND]"
            echo
            echo "Commands:"
            echo "  (none)    Deploy the Plug-and-Play RAG system"
            echo "  down      Stop the system"
            echo "  logs      Show system logs"
            echo "  restart   Restart the system"
            echo "  status    Show container status"
            echo "  help      Show this help message"
            exit 0
            ;;
    esac
    
    # Main deployment flow
    check_requirements
    check_docker
    load_env
    validate_config
    build_image
    deploy_app
    wait_for_health
    show_status
}

# Run main function
main "$@"
