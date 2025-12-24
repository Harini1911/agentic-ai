import os
from google import genai
from lmnr import Laminar
from dotenv import load_dotenv

load_dotenv()

# Initialize Laminar
# Ensure LMNR_PROJECT_API_KEY is set in your environment
Laminar.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))

# Initialize Client
# Ensure you have set the GOOGLE_API_KEY environment variable or replace with your key
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
