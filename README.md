# Cloud Pathology AI Microservice

This microservice is part of the Cloud Pathology AI platform. It is built using FastAPI and serves as a crucial component for AI-based pathology analysis.

This marks the initial phase of the project, focusing on setting up the FastAPI structure, dependencies, and deployment configuration.

Initial Setup and Installation

1. Clone the Repository

   ```shell
    git clone https://clvc@dev.azure.com/clvc/Cloud%20Pathology/_git/CloudPathologyAI
    cd CloudPathologyAI
   ```

2. Create and Activate Virtual Environment
   - For macOS/Linux:
     ```
     python3 -m venv env
     source env/bin/activate
     ```
   - For Windows:
     ```
     python -m venv env
     .\env\Scripts\activate
     ```
3. Install Dependencies

   ```
   pip install -r requirements.txt
   ```

   To Verify Installations, run:

   ```
    pip freeze
   ```

4. Running the Application Locally

   ```
   uvicorn app.main:app --reload
   ```

   Access the app on http://localhost:8000

5. Cloud Pathology AI API Authentication

   - install the python-dotenv from requirement.txt
   - Run the application using : uvicorn app.main:app --reload
   - Use postman to test the functionality with URL: http://127.0.0.1:8000/insert_user?first_name=rucha&last_name=abc&email=abcdh@gmail.com and method as POST
   - Add paramaters: first_name, last_name, email and desired values for these parameters
   - Add key value as X-API-Key in header and it's value will be in .env file
   - You can also run the unit test cases in test_main.py file for valid and invalid api

6. To check the code coverage locally:

   - To check code coverage of root directory:
     pytest --cov=. --cov-report=term-missing
   - To check individual test file code coverage:
     pytest tests/your_file_name.py
   - To generate the HTML report:
     pytest --cov=. --cov-report=html
   - To open the genarated html report:
     open htmlcov/index.html
   - When you open the html report, you can see the files along with their missing lines for code coverage in red color

7. Swagger documentation:
   ```
   http://localhost:8000/docs
   ```
