import pytest
from unittest.mock import patch
from app.llm_api.openai_client import generate_text

class MockResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

class MockException(Exception):
    def __init__(self, response):
        self.response = response

@pytest.mark.asyncio
async def test_generate_text_valid():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    expected_response = "Mocked text"

    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices[0].message = expected_response

        response = await generate_text(prompt, model)

        assert response == expected_response
        mock_client.chat.completions.create.assert_called_once_with(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1e-5
        )

@pytest.mark.asyncio
async def test_generate_text_rate_limit_error():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    mock_response = MockResponse(429, "Rate limit exceeded")
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = MockException(mock_response)
        response = await generate_text(prompt, model)
        assert response == "Rate limit exceeded. Please try again later."


@pytest.mark.asyncio
async def test_generate_text_authentication_error():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    mock_response = MockResponse(401, "Authentication error")
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = MockException(mock_response)
        response = await generate_text(prompt, model)
        assert response is None

@pytest.mark.asyncio
async def test_generate_text_permission_denied():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    mock_response = MockResponse(403, "Permission denied")
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = MockException(mock_response)
        response = await generate_text(prompt, model)
        assert response is None

@pytest.mark.asyncio
async def test_generate_text_resource_not_found():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    mock_response = MockResponse(404, "Resource not found")
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = MockException(mock_response)
        response = await generate_text(prompt, model)
        assert response is None

@pytest.mark.asyncio
async def test_generate_text_unprocessable_entity():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    mock_response = MockResponse(422, "Unprocessable entity")
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = MockException(mock_response)
        response = await generate_text(prompt, model)
        assert response is None

@pytest.mark.asyncio
async def test_generate_text_unhandled_api_error():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    mock_response = MockResponse(500, "Unhandled API error")
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = MockException(mock_response)
        response = await generate_text(prompt, model)
        assert response is None

@pytest.mark.asyncio
async def test_generate_text_general_error():
    prompt = "Tell me a joke."
    model = "gpt-4o"
    
    with patch('app.llm_api.openai_client.client') as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("General error")
        response = await generate_text(prompt, model)
        assert response is None