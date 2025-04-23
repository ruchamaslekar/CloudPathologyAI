# ScyllaDB Setup on Local Sandbox

## Prerequisites
1. Docker and Docker Compose installed.
2. Clone the repository.

## Steps

1. **Run ScyllaDB**:
   - Run `docker-compose up -d` in the root directory of your project.
   - ScyllaDB will run on port `9042`. - You can check this with - `docker ps` 
   - pip install -r requirements.txt

2. **Access ScyllaDB**:
   docker exec -it <container_name_or_id> cqlsh

3. **Create the Keyspace and Migration Script**

#### Step 3.1: Create Keyspace and Tables in ScyllaDB
    - Run `docker exec -it <container_name> cqlsh -f /migrations/migration-ts.cql`
    - Created an example users table

4. **Run FASTAPI APP**:
    uvicorn main:app --reload
    You can test it by : curl -X POST "http://127.0.0.1:8000/insert_user/?first_name=John&last_name=Doe&email=john.doe@example.com"


