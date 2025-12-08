import os
import sys
from typing import List, Optional, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from lmnr import Laminar, observe
import json
import re
from tools import FileProcessor, process_audio, generate_audio

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
    label: str = Field(description="A short label for the research point")
    source: str = Field(description="The source document or section")
    source_link: Optional[str] = Field(default=None, description="Direct URL link to the source if available")
    content: str = Field(description="The extracted information")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")

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

@observe()
def perform_grounded_search(query: str, active_files: List[types.File] = []) -> tuple[ResearchResult, List[str]]:
    """
    Performs a Google Search grounded query and returns structured ResearchResult
    and a list of web sources found. Can include active_files context.
    """
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    prompt = f"""
    Research the following query using Google Search.
    Return the result STRICTLY as a valid JSON object matching this structure:
    {{
        "points": [
            {{
                "label": "Topic Label",
                "source": "Source Name",
                "source_link": "Direct URL",
                "content": "extracted information",
                "confidence": 0.95
            }}
        ],
        "summary": "Concise summary of findings"
    }}
    
    Query: {query}
    """
    
    # prompt = f"""
    # Research the following query using Google Search.

    # Query: {query}
    # """

    request_contents = [prompt]
    if active_files:
        print("Including file context in search...")
        for file in active_files:
            request_contents.append(file)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=request_contents,
        config=types.GenerateContentConfig(
            tools=[grounding_tool],
            # response_mime_type="application/json" # Not supported with tools
            
        ),
    )
    
    # Extract web sources from metadata
    web_sources = []
    if response.candidates and response.candidates[0].grounding_metadata:
        chunks = response.candidates[0].grounding_metadata.grounding_chunks
        if chunks:
            web_sources = [c.web.uri for c in chunks if c.web and c.web.uri]
            web_sources = list(dict.fromkeys(web_sources))

    # Parse JSON from text
    try:
        text = response.text
        # Cleanup code blocks if present
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```", "", text)
        data = json.loads(text)
        return ResearchResult(**data), web_sources
    except Exception as e:
        print(f"Error parsing JSON from search result: {e}")
        # Return a fallback result
        return ResearchResult(points=[], summary=f"Raw Search Result: {response.text}"), web_sources



def main_loop():
    print("Welcome to the Multi-Modal Research Agent!")
    print("Type your query or use commands:")
    print("  /file <path>  : Upload a file (PDF, Audio, etc.)")
    print("  /speak <text> : Generate audio from text")
    print("  /search <query>: Google Search with grounding")
    print("  exit / quit   : Exit the agent")
    
    active_files = []
    
    try:
        while True:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting...")
                break
                
            if user_input.startswith("/file"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /file <path>")
                    continue
                
                path = parts[1].strip()
                if not os.path.exists(path):
                    print(f"File not found: {path}")
                    continue
                
                try:
                    print(f"Processing file: {path}...")
                    # Determine type based on extension or just try upload
                    # Simple heuristic: if likely audio, use process_audio, else generic upload
                    if path.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
                        uploaded_file = process_audio(client, path)
                    else:
                        processor = FileProcessor(client)
                        uploaded = processor.upload_file(path)
                        uploaded_file = processor.wait_for_processing(uploaded.name)
                        
                    active_files.append(uploaded_file)
                    print(f"File added to context: {uploaded_file.display_name or uploaded_file.name}")
                    
                except Exception as e:
                    print(f"Error processing file: {e}")
                continue


            if user_input.startswith("/speak"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /speak <text>")
                    continue
                
                text_to_speak = parts[1].strip()
                print(f"Generating audio for: '{text_to_speak}'...")
                generate_audio(client, text_to_speak)
                continue

            if user_input.startswith("/search"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /search <query>")
                    continue
                
                query = parts[1].strip()
                print(f"Searching Google for: '{query}'...")
                try:
                    result, sources = perform_grounded_search(query, active_files)
                    
                    # Convert to Dictionary (JSON-like structure)
                    points_dict = {p.label: p.model_dump() for p in result.points}
                    
                    print("\n--- Search Results ---")
                    print(f"Summary: {result.summary}\n")
                    print("Key Points:")
                    for label, data in points_dict.items():
                        print(f"- {label}: {data['content']}")
                        print(f"  Source: {data['source']}")
                        if data.get('source_link'):
                            print(f"  Link: {data['source_link']}")
                        print(f"  Confidence: {data['confidence']}")

                    if sources:
                        print("\n--- Web Sources ---")
                        for i, source in enumerate(sources, 1):
                            print(f"{i}. {source}")
                            
                except Exception as e:
                    print(f"Error during search: {e}")
                continue

            # Treat as query
            print("Analyzing...")
            try:
                result = analyze_query(user_input, files=active_files)
                
                # Convert to Dictionary (JSON-like structure)
                points_dict = {p.label: p.model_dump() for p in result.points}
                
                print("\n--- Research Results ---")
                print(f"Summary: {result.summary}\n")
                print("Key Points:")
                for label, data in points_dict.items():
                    print(f"- {label}: {data['content']} (Confidence: {data['confidence']})")
                    
            except Exception as e:
                print(f"Error during analysis: {e}")

    finally:
        # Cleanup
        if active_files:
            print("\nCleaning up uploaded files...")
            processor = FileProcessor(client)
            for f in active_files:
                processor.delete_file(f.name)

if __name__ == "__main__":
    main_loop()
