<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Chat with Your Data - RAG System

This project is a Retrieval-Augmented Generation (RAG) system built with FastAPI that:
- Connects to PostgreSQL and MongoDB databases
- Creates embeddings from structured data
- Uses ChromaDB as vector database for similarity search
- Integrates with Google Gemini AI for intelligent responses
- Provides streaming responses and maintains chat history per user

## Key Components:
- Database connectors for PostgreSQL and MongoDB
- Vector embeddings using sentence-transformers
- ChromaDB for vector storage and retrieval
- Gemini AI integration with optimized prompts
- FastAPI endpoints with streaming support
- User-based chat history management

## Development Guidelines:
- Use async/await patterns for database and API operations
- Implement proper error handling and logging
- Follow FastAPI best practices for API design
- Use Pydantic models for request/response validation
- Maintain clean separation between database, embedding, and AI components
