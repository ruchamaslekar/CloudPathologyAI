from dotenv import load_dotenv
import logging
from openai import OpenAI
import os

logging.basicConfig(filename="app.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")     
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)
async def generate_text(prompt, model="gpt-4o"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=1e-5
        )
        return response.choices[0].message
    except Exception as e:
        # This assumes that the exception includes the response object
        if hasattr(e, 'response'):
            status_code = e.response.status_code
            err_msg = f"Error occurred: {e.response.text}"

            # Handle specific status codes
            if status_code == 429:
                logger.error("Rate limit exceeded. Try again later.")
                return "Rate limit exceeded. Please try again later."
            elif status_code == 401: 
                logger.error("Authentication error. Check your API key.")
                return None
            elif status_code == 403:
                logger.error("Permission denied.")
                return None
            elif status_code == 404:
                logger.error("Resource not found.")
                return None
            elif status_code == 422:
                logger.error("Unprocessable entity.")
                return None
            else:
                logger.error(f"Unhandled API error: {err_msg}")
                return None
        else:
            logger.error(f"General error: {str(e)}")
            return None
