import os
import sys
from typing import List, Optional, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from lmnr import Laminar, observe
from tools import FileProcessor, process_audio

# Load environment variables
load_dotenv()

LAMINAR_API_KEY = os.getenv("LAMINAR_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

# Initialize Laminar
if LAMINAR_API_KEY:
    Laminar.initialize(project_api_key=LAMINAR_API_KEY)
else:
    print("Warning: LAMINAR_API_KEY not found in .env")

# Initialize Gemini Client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("Error: GOOGLE_API_KEY not found in .env")
    sys.exit(1)

# Define Pydantic Models
class ResearchPoint(BaseModel):
    label: str = Field(..., description="A short topic label or title for this point.")
    source: str = Field(..., description="The source of the information (e.g., filename, audio timestamp).")
    content: str = Field(..., description="The extracted key point or information.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")

class ResearchResult(BaseModel):
    points: List[ResearchPoint] = Field(..., description="List of extracted research points.")
    summary: str = Field(..., description="A concise summary of the findings.")

@observe()
def analyze_query(query: str, files: List[types.Part] = None) -> ResearchResult:

    if files is None:
        files = []
    
    prompt = f"""
    Analyze the following query and provided context (if any).
    Extract key research points and provide a summary.
    
    Query: {query}
    """
    
    contents = [prompt]
    if files:
        contents.extend(files)
     
    # print(f"contents-----------------: {contents}")
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResearchResult,
        ),
    )
    
    return response.parsed

if __name__ == "__main__":
    # Basic test
    try:
        # Example 1: Text only
        print("--- Text Only ---")
        result = analyze_query("What is the capital of France?")
        print(result)

        # Example 2: With PDF (if exists)
        pdf_path = "sample_research.pdf"
        if os.path.exists(pdf_path):
            print(f"\n--- With File ({pdf_path}) ---")
            processor = FileProcessor(client)
            # Upload file
            uploaded_file = processor.upload_file(pdf_path)
            # Wait for it to be active
            active_file = processor.wait_for_processing(uploaded_file.name)
            
            # Analyze with file
            result_with_file = analyze_query("Applications of AI in healthcare.", files=[active_file])
            print(result_with_file)
            
            # Cleanup
            processor.delete_file(uploaded_file.name)
            
    except Exception as e:
        print(f"Error: {e}")
