import google.generativeai as genai
from typing import List, Dict, Any, AsyncIterator
import logging
import asyncio
from ..config import settings
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class GeminiClient(BaseLLMClient):
    """Client for interacting with Google Gemini AI."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Gemini client."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS,
                }
            )
            logger.info(f"Gemini client initialized with model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
            raise
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the RAG system."""
        return """You are an intelligent assistant that helps users query and understand their data using a Retrieval-Augmented Generation (RAG) approach.

Your role:
1. Analyze the user's question carefully
2. Use the provided context from their database to answer accurately  
3. Be specific and cite information from the context when possible
4. If the context doesn't contain enough information, clearly state this
5. Provide clear, structured, and helpful responses
6. When dealing with numerical data, provide summaries or insights when relevant
7. For dates and timestamps, format them in a user-friendly way

Context formatting:
- Each context document contains database records with various fields
- Pay attention to field names and their values
- Consider relationships between different data points
- If multiple records are provided, look for patterns or trends

Response guidelines:
- Be conversational but professional
- Use bullet points or numbered lists when appropriate
- Highlight important findings
- If you notice inconsistencies in the data, mention them
- Always be truthful about the limitations of your knowledge based on the provided context"""
    
    def _build_user_prompt(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        chat_history: List[Dict[str, Any]] = None
    ) -> str:
        """Build the user prompt with context and history."""
        prompt_parts = []
        
        # Add chat history if available
        if chat_history:
            prompt_parts.append("=== PREVIOUS CONVERSATION ===")
            for msg in chat_history[-5:]:  # Include last 5 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")
        
        # Add context documents
        if context_documents:
            prompt_parts.append("=== RELEVANT DATA FROM YOUR DATABASE ===")
            for i, doc in enumerate(context_documents, 1):
                metadata = doc.get('metadata', {})
                content = doc.get('content', '')
                
                prompt_parts.append(f"Document {i}:")
                prompt_parts.append(f"Content: {content}")
                
                if metadata:
                    prompt_parts.append("Raw Data:")
                    for key, value in metadata.items():
                        if value is not None:
                            prompt_parts.append(f"  - {key}: {value}")
                
                prompt_parts.append("")
        else:
            prompt_parts.append("=== NO RELEVANT DATA FOUND ===")
            prompt_parts.append("Note: No relevant data was found in your database for this question.")
            prompt_parts.append("")
        
        # Add current question
        prompt_parts.append("=== CURRENT QUESTION ===")
        prompt_parts.append(question)
        prompt_parts.append("")
        prompt_parts.append("Please provide a helpful and accurate response based on the above information.")
        
        return "\n".join(prompt_parts)
    
    async def generate_response(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        chat_history: List[Dict[str, Any]] = None
    ) -> str:
        """Generate a response using Gemini."""
        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(question, context_documents, chat_history)
            
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate response asynchronously
            def generate_sync():
                response = self.model.generate_content(full_prompt)
                return response.text
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, generate_sync)
            
            logger.info("Generated response using Gemini")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            raise
    
    async def generate_response_stream(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        chat_history: List[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Gemini."""
        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(question, context_documents, chat_history)
            
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate streaming response
            def generate_stream_sync():
                response = self.model.generate_content(
                    full_prompt,
                    stream=True
                )
                return response
            
            loop = asyncio.get_event_loop()
            stream_response = await loop.run_in_executor(None, generate_stream_sync)
            
            # Yield chunks asynchronously
            for chunk in stream_response:
                if chunk.text:
                    yield chunk.text
            
            logger.info("Generated streaming response using Gemini")
            
        except Exception as e:
            logger.error(f"Error generating streaming response with Gemini: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test the Gemini API connection."""
        try:
            test_prompt = "Hello, can you confirm you're working?"
            
            def test_sync():
                response = self.model.generate_content(test_prompt)
                return response.text
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, test_sync)
            
            return bool(response and len(response.strip()) > 0)
            
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the Gemini client."""
        return {
            "type": "gemini",
            "model": settings.GEMINI_MODEL,
            "temperature": settings.GEMINI_TEMPERATURE,
            "max_tokens": settings.GEMINI_MAX_TOKENS,
            "has_api_key": bool(self.api_key),
            "initialized": self.model is not None
        }
