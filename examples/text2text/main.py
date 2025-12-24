import logging
import os

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# File handler
file_handler = logging.FileHandler("logs/main.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

def main():
    logger.info("Hello from text2text!")
    print("Hello from text2text!")


if __name__ == "__main__":
    main()
