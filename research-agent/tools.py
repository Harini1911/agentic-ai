import os
import time
from pathlib import Path
from google import genai
from google.genai import types
from pydub import AudioSegment

class FileProcessor:
    def __init__(self, client: genai.Client):
        self.client = client

    def upload_file(self, path: str, mime_type: str = None) -> types.File:
        """Uploads a file to Gemini."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        print(f"Uploading {file_path}...")
        uploaded_file = self.client.files.upload(file=file_path)
        print(f"Uploaded file: {uploaded_file.name}")
        return uploaded_file

    def wait_for_processing(self, file_name: str):
        """Waits for the file to be processed."""
        print(f"Waiting for {file_name} to be processed...")
        while True:
            file = self.client.files.get(name=file_name)
            if file.state.name == "ACTIVE":
                print(f"File {file_name} is active.")
                return file
            elif file.state.name == "FAILED":
                raise Exception(f"File {file_name} failed to process.")
            
            time.sleep(2)

    def delete_file(self, file_name: str):
        """Deletes a file from Gemini."""
        try:
            self.client.files.delete(name=file_name)
            print(f"Deleted file: {file_name}")
        except Exception as e:
            print(f"Error deleting file {file_name}: {e}")

