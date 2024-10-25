import os
import voyageai as voyageai
from voyageai.api_resources import APIResource
# llm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
voyager_api_key = os.getenv("VOYAGER_API_KEY")