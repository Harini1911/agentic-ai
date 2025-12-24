from google import genai
import os
import logging

# Setup logger
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO) # Removed to prevent duplicate logs in importing modules

import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))