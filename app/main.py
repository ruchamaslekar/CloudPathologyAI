from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from app.llm_api.openai_client import generate_text
from auth.auth import get_api_key
from database.connection import ScyllaConnection
from database.query_runner import QueryRunner
from uuid import uuid4
from app.routers.case_data import router as case_data_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Establish connection to ScyllaDB
    conn = ScyllaConnection(keyspace='dev_keyspace')
    conn.connect()
    app.state.conn = conn
    yield
    # Shutdown: Close ScyllaDB connection
    app.state.conn.close()

app = FastAPI(lifespan=lifespan)
app.include_router(case_data_router)

#Temporary endpoint for testing 
@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Temporary endpoint to test API key authentication; returns user inserted if valid.
@app.post("/insert_user/")
async def insert_user(first_name: str, last_name: str, email: str, api_key: str = Depends(get_api_key)):
    print("Insert user endpoint called with:", first_name, last_name, email)  # Debug statement
    runner = QueryRunner(connection=app.state.conn)
    runner.run_query("USE dev_keyspace") 
    query = "INSERT INTO users (user_id, first_name, last_name, email) VALUES (%s, %s, %s, %s)"
    runner.run_query(query, (uuid4(), first_name, last_name, email))
    return {"status": "user inserted"}

# Endpoint to generate response based on prompt
@app.get("/generate")
async def generate_text_route(prompt: str, user: dict = Depends(get_api_key)):
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    result = await generate_text(prompt)
    return {"result": result}


