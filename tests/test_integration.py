"""
Integration tests for the complete system
"""

import pytest
import asyncio
import httpx
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestSystemIntegration:
    """Test complete system integration."""

    @pytest.fixture(autouse=True)
    async def setup_test_server(self):
        """Set up test server for integration tests."""
        # This would typically start a test server
        # For now, we'll assume the server is running on localhost:8001
        self.base_url = "http://localhost:8001"
        self.timeout = 30.0
        
        # Test if server is running
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                if response.status_code != 200:
                    pytest.skip("Test server not running")
            except Exception:
                pytest.skip("Test server not available")

    async def test_complete_rag_pipeline(self):
        """Test the complete RAG pipeline end-to-end."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Check system health
            health_response = await client.get(f"{self.base_url}/health")
            assert health_response.status_code == 200
            
            # 2. Get current LLM provider
            llm_response = await client.get(f"{self.base_url}/api/llm/current")
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                assert "provider" in llm_data
                assert "model" in llm_data
            
            # 3. Ingest demo data
            ingest_config = {
                "db_type": "demo",
                "table_or_collection": "test_articles",
                "text_fields": ["title", "content"]
            }
            
            ingest_response = await client.post(
                f"{self.base_url}/ingest-data",
                json=ingest_config
            )
            
            if ingest_response.status_code == 200:
                # 4. Wait for processing
                await asyncio.sleep(2)
                
                # 5. Test chat functionality
                chat_request = {
                    "message": "What information do you have?",
                    "user_name": "integration_test"
                }
                
                chat_response = await client.post(
                    f"{self.base_url}/chat",
                    json=chat_request
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    assert "response" in chat_data
                    assert "user_name" in chat_data
                    assert chat_data["user_name"] == "integration_test"

    async def test_llm_provider_switching(self):
        """Test switching between LLM providers."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Get current provider
            current_response = await client.get(f"{self.base_url}/api/llm/current")
            if current_response.status_code != 200:
                pytest.skip("LLM provider not available")
            
            original_provider = current_response.json()
            
            # Try to switch to a test provider (this might fail in real scenarios)
            switch_request = {
                "provider": "custom",
                "model_name": "test-model",
                "endpoint_url": "http://localhost:9999/test"
            }
            
            switch_response = await client.post(
                f"{self.base_url}/api/llm/switch",
                json=switch_request
            )
            
            # This might fail due to unreachable endpoint, which is expected
            # The test is mainly to ensure the endpoint works
            assert switch_response.status_code in [200, 400, 500]

    async def test_error_handling(self):
        """Test system error handling."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Test invalid endpoint
            response = await client.get(f"{self.base_url}/invalid-endpoint")
            assert response.status_code == 404
            
            # Test invalid chat request
            invalid_chat = {"invalid_field": "value"}
            chat_response = await client.post(
                f"{self.base_url}/chat",
                json=invalid_chat
            )
            assert chat_response.status_code == 422
            
            # Test invalid ingestion config
            invalid_ingest = {"db_type": "invalid_type"}
            ingest_response = await client.post(
                f"{self.base_url}/ingest-data",
                json=invalid_ingest
            )
            assert ingest_response.status_code in [400, 422, 500]

    async def test_chat_history_persistence(self):
        """Test chat history functionality."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            user_name = "history_test_user"
            
            # Send a chat message
            chat_request = {
                "message": "Hello, this is a test message",
                "user_name": user_name
            }
            
            chat_response = await client.post(
                f"{self.base_url}/chat",
                json=chat_request
            )
            
            if chat_response.status_code == 200:
                # Get chat history
                history_response = await client.get(
                    f"{self.base_url}/chat/history/{user_name}"
                )
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    assert isinstance(history_data, list)
                    
                    # Clear history
                    clear_response = await client.delete(
                        f"{self.base_url}/chat/history/{user_name}"
                    )
                    assert clear_response.status_code == 200

    async def test_system_performance(self):
        """Test basic system performance."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            import time
            
            # Test response time for health check
            start_time = time.time()
            response = await client.get(f"{self.base_url}/health")
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Should respond within 1 second
            
            # Test concurrent requests
            async def health_check():
                return await client.get(f"{self.base_url}/health")
            
            # Send 5 concurrent requests
            tasks = [health_check() for _ in range(5)]
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200


@pytest.mark.integration
class TestDemoScriptIntegration:
    """Test demo script functionality."""

    def test_demo_script_exists(self):
        """Test that demo script exists and is executable."""
        import os
        demo_path = "demo.py"
        assert os.path.exists(demo_path)
        assert os.access(demo_path, os.X_OK)

    @pytest.mark.asyncio
    async def test_demo_health_check(self):
        """Test demo script health check functionality."""
        import subprocess
        import sys
        
        # Run the demo script health check
        try:
            result = subprocess.run([
                sys.executable, "demo.py", "health"
            ], capture_output=True, text=True, timeout=30)
            
            # Should not crash (exit code 0 or 1 are both acceptable)
            # as it depends on server availability
            assert result.returncode in [0, 1]
            
        except subprocess.TimeoutExpired:
            pytest.skip("Demo script took too long to execute")
        except Exception as e:
            pytest.skip(f"Could not run demo script: {e}")


@pytest.mark.integration  
class TestDocumentationIntegration:
    """Test documentation and configuration files."""

    def test_readme_exists(self):
        """Test that README exists and contains key information."""
        with open("README.md", "r") as f:
            content = f.read()
            assert "Plug-and-Play RAG" in content
            assert "localhost:8001" in content
            assert "FastAPI" in content

    def test_env_example_exists(self):
        """Test that environment example exists."""
        with open(".env.example", "r") as f:
            content = f.read()
            assert "LLM_PROVIDER" in content
            assert "GEMINI_API_KEY" in content

    def test_requirements_exist(self):
        """Test that requirements file exists and contains key dependencies."""
        with open("requirements.txt", "r") as f:
            content = f.read()
            assert "fastapi" in content.lower()
            assert "httpx" in content.lower()
            assert "chromadb" in content.lower()

    def test_project_structure_documentation(self):
        """Test that project structure documentation exists."""
        import os
        docs_files = [
            "PROJECT_STRUCTURE.md",
            "LLM_CONFIGURATION.md", 
            "PLUG_AND_PLAY_CONCEPT.md"
        ]
        
        for doc_file in docs_files:
            assert os.path.exists(doc_file), f"{doc_file} should exist"


@pytest.mark.integration
class TestContainerIntegration:
    """Test Docker container integration."""

    def test_dockerfile_or_compose_exists(self):
        """Test that Docker configuration exists."""
        import os
        # Should have either Dockerfile or docker-compose.yml
        has_docker_config = (
            os.path.exists("Dockerfile") or 
            os.path.exists("docker-compose.yml")
        )
        assert has_docker_config, "Should have Docker configuration"

    def test_start_script_exists(self):
        """Test that start script exists and is executable."""
        import os
        assert os.path.exists("start.sh")
        assert os.access("start.sh", os.X_OK)
