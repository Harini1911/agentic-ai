import json
import time
import os
import logging
from google import genai
from google.genai import types
from config import client

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# File handler
file_handler = logging.FileHandler("logs/text_generation_sys.log")
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[LOGGED] %(message)s'))
logger.addHandler(stream_handler)


def text_gen_thinking(prompt):
    start_time = time.time()

    # Log request
    request_record = {
        "event": "REQUEST",
        "prompt": prompt,
        "model": "gemini-2.5-flash",
        "config": {
            "system_instruction":"You are a Poet. You write poetic responses.",
            "temperature": 0.7
        },
        "timestamp": time.time(),
    }
    logger.info(json.dumps(request_record))

    # Send request to Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="You are a Math Teacher. Help me solve problems", #system instruction to guide the model
            temperature=0.1), #temperature controls creativity
        contents="0/0=?"
    )

    end_time = time.time()

    # Log response
    response_record = {
        "event": "RESPONSE",
        "prompt": prompt,
        "response_text": response.text,
        "model": "gemini-2.5-flash",
        "latency_ms": round((end_time - start_time) * 1000, 2),
        "timestamp": time.time(),
    }
    logger.info(json.dumps(response_record))

    return response.text


answer = text_gen_thinking("How does AI work?")
print("\nFINAL ANSWER:\n", answer)
