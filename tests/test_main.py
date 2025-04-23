import os
from uuid import uuid4
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from auth.auth import get_api_key

client = TestClient(app)

@pytest.fixture(autouse=True)
def set_openai_key():
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test_api_key")   # Use the test API key directly for testing
    yield
    del os.environ["OPENAI_API_KEY"]

@pytest.mark.asyncio
class TestMain:

    @pytest.mark.asyncio
    async def test_generate_text_route_success(self):
        # Mock the generate_text function
        async def mock_generate_text(prompt: str):
            return "Mocked text"

        # Apply the mocks
        with patch('app.main.generate_text', new=mock_generate_text):
            # Override the get_api_key dependency to simulate valid API key
            app.dependency_overrides[get_api_key] = lambda: "test_api_key"

            headers = {"X-API-Key": "test_api_key"}
            response = client.get("/generate?prompt=Tell me a joke.", headers=headers)

            # Check response status code and content
            assert response.status_code == 200, f"Expected 200 but got {response.status_code} with response {response.json()}"
            assert response.json() == {"result": "Mocked text"}

            # Clear dependency override after the test
            app.dependency_overrides.clear()

    async def test_generate_text_route_unauthorized(self):
        # Override the get_api_key dependency to simulate invalid API key
        app.dependency_overrides[get_api_key] = lambda: None
        
        headers = {"X-API-Key": "invalid_api_key"}
        response = client.get("/generate?prompt=Tell me a joke.", headers=headers)
        
        # Check response status code and content
        assert response.status_code == 403, f"Expected 403 but got {response.status_code} with response {response.json()}"
        assert response.json() == {"detail": "Unauthorized access"}

        # Clear dependency override after the test
        app.dependency_overrides.clear()



