
import logging
import os
from google import genai
from config import client

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# File handler
file_handler = logging.FileHandler("logs/text_gen.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

def generate(prompt):
    logger.info(f"REQUEST: {{'prompt': '{prompt}'}}")

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    logger.info(f"RESPONSE: {{'response': '{resp.text}'}}")
    return resp.text

print(generate("Tell me places to visit in chennai."))









# response = client.models.generate_content(
#     model="gemini-2.5-flash", contents="Explain how AI works in a few words"
# )
# print(response.text)

# def generate_and_log(contents, config=None):
#     print("=== REQUEST ===")
#     print({"contents": contents, "config": config})
#     resp = client.models.generate_content(model="gemini-2.5-flash", contents=contents, config=config)
#     print("=== RESPONSE ===")
#     print(resp)
#     return resp

# # Test
# r = generate_and_log("Hello, world!")
# print(r.text)

