import json
import time
import os
import logging
from PIL import Image
from google import genai
from google.genai import types
from config import client

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# File handler
file_handler = logging.FileHandler("logs/text_generation_multimodal.log")
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[LOGGED] %(message)s'))
logger.addHandler(stream_handler)


def multimodal_text_gen(prompt, image_path, system_instruction=None):
    start_time = time.time()

    # Load image
    image = Image.open(image_path)

    # --- Build config dynamically ---
    generation_config = {
        "system_instruction": system_instruction,
        "thinking_budget": -1,     # dynamic thinking
    }

    # Log request
    request_record = {
        "event": "REQUEST",
        "prompt": prompt,
        "image_path": image_path,
        "model": "gemini-2.5-flash",
        "config": generation_config,
        "timestamp": time.time(),
    }
    logger.info(json.dumps(request_record))

    # --- Build Gemini request ---
    contents = [image, prompt]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_budget=-1)
        ),
    )

    end_time = time.time()

    # Log response
    response_record = {
        "event": "RESPONSE",
        "prompt": prompt,
        "image_path": image_path,
        "response_text": response.text,
        "model": "gemini-2.5-flash",
        "latency_ms": round((end_time - start_time) * 1000, 2),
        "timestamp": time.time(),
    }
    logger.info(json.dumps(response_record))

    return response.text


# Example Usage
answer = multimodal_text_gen(
    prompt="Tell me about this instrument",
    image_path="./image.png",
    system_instruction="You are expert in describing images."
)

print("\nFINAL ANSWER:\n", answer)
