import os
from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader

app = FastAPI()

# Load environment variables, define API key header, and validate the API key from headers.
load_dotenv()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.getenv('SECURITY_KEY'):
        raise HTTPException(status_code=403, detail="Could not validate API key")
    return api_key

