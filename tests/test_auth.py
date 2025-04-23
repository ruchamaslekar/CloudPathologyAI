import os
import pytest
from fastapi import HTTPException
from auth.auth import get_api_key  # Adjust the import path as necessary

# Fixture to set and tear down the SECURITY_KEY environment variable
@pytest.fixture(autouse=True)
def set_security_key():
    os.environ['SECURITY_KEY'] = '94ba82602b41a4a700f40f4ba3dda419e099709dcf965703ca87c4c4ce1c4af1'
    yield
    del os.environ['SECURITY_KEY']  # Clean up after tests

@pytest.mark.asyncio
async def test_valid_api_key():
    api_key = os.environ['SECURITY_KEY']
    result = await get_api_key(api_key)
    assert result == api_key 

@pytest.mark.asyncio
async def test_invalid_api_key():
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key("invalid_api_key")
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"

@pytest.mark.asyncio
async def test_missing_api_key():
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key(None)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"

@pytest.mark.asyncio
async def test_empty_api_key():
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key("")
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"

@pytest.mark.asyncio
async def test_api_key_with_whitespace():
    api_key = f"  {os.environ['SECURITY_KEY']}  "  # Leading and trailing spaces
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key(api_key)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"

@pytest.mark.asyncio
async def test_api_key_case_sensitivity():
    api_key = os.environ['SECURITY_KEY'].upper()  # Uppercase version of the key
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key(api_key)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"

@pytest.mark.asyncio
async def test_env_variable_not_set(monkeypatch):
    # Temporarily remove the SECURITY_KEY environment variable for this test
    monkeypatch.delenv('SECURITY_KEY', raising=False)
    
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key("any_key")  # Provide any key
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"

@pytest.mark.asyncio
async def test_different_key():
    # Test with a completely different key
    different_key = "some_other_key"
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key(different_key)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Could not validate API key"
