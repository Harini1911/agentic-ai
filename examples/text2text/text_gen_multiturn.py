import time
import json
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
file_handler = logging.FileHandler("logs/text_generation_multiturn.log")
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[LOGGED] %(message)s'))
logger.addHandler(stream_handler)


def multi_turn_chat():
    # Create chat session
    chat = client.chats.create(model="gemini-2.5-flash")

    def send_and_log(user_message):

        start_time = time.time()

        # Log request
        request_record = {
            "event": "REQUEST",
            "type": "CHAT_MESSAGE",
            "input_message": user_message,
            "model": "gemini-2.5-flash",
            "timestamp": time.time(),
        }
        logger.info(json.dumps(request_record))

        # Send message to Gemini chat session
        response = chat.send_message(user_message)

        end_time = time.time()

        # Log response
        response_record = {
            "event": "RESPONSE",
            "type": "CHAT_MESSAGE",
            "input_message": user_message,
            "response_text": response.text,
            "latency_ms": round((end_time - start_time) * 1000, 2),
            "timestamp": time.time(),
        }
        logger.info(json.dumps(response_record))

        print("\nMODEL:", response.text)
        return response

    print("USER: I have 2 dogs in my house.")
    send_and_log("I have 2 dogs in my house.")

    print("\nUSER: How many paws are in my house?")
    send_and_log("How many paws are in my house?")

    print("\n--- CHAT HISTORY ---\n")

    for msg in chat.get_history():

        role = msg.role
        parts = msg.parts[0].text if msg.parts else ""

        # Log each history event
        history_record = {
            "event": "CHAT_HISTORY",
            "role": role,
            "message": parts,
            "timestamp": time.time()
        }
        logger.info(json.dumps(history_record))

        # Print to terminal
        print(f"{role}: {parts}")


# Run example
multi_turn_chat()
