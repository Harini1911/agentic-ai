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
file_handler = logging.FileHandler("logs/text_generation_streaming.log")
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[LOGGED] %(message)s'))
logger.addHandler(stream_handler)


def stream_text_gen(prompt, system_instruction=None):
    start_time = time.time()

    # --- Build config payload for logs ---
    generation_config = {
        "system_instruction": system_instruction,
        "thinking_budget": -1,      # dynamic thinking
    }

    # --- Log request ---
    request_record = {
        "event": "REQUEST",
        "prompt": prompt,
        "model": "gemini-2.5-flash",
        "config": generation_config,
        "timestamp": time.time(),
    }
    logger.info(json.dumps(request_record))

    # --- Start streaming ---
    response_stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_budget=-1)
        ),
    )

    full_output = ""

    for chunk in response_stream:
        text = chunk.text or ""
        full_output += text

        # Log every streamed chunk
        chunk_record = {
            "event": "STREAM_CHUNK",
            "chunk_text": text,
            "model": "gemini-2.5-flash",
            "timestamp": time.time(),
        }
        logger.info(json.dumps(chunk_record))

        print(text, end="")   # real-time console output

    end_time = time.time()

    # --- Log final response ---
    response_record = {
        "event": "FINAL_RESPONSE",
        "prompt": prompt,
        "response_text": full_output,
        "model": "gemini-2.5-flash",
        "latency_ms": round((end_time - start_time) * 1000, 2),
        "timestamp": time.time(),
    }
    logger.info(json.dumps(response_record))

    return full_output


# Example usage
print("\n\n--- STREAM OUTPUT ---")
answer = stream_text_gen("Explain how agentic AI works")
print("\n\nFINAL ANSWER:\n", answer)
