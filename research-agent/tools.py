import os
import time
from pathlib import Path
from google import genai
from google.genai import types
from google.genai import types
import wave
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


def process_audio(client: genai.Client, audio_path: str) -> types.File:
    """
    Processes an audio file: converts to mp3 using pydub if needed, 
    and uploads to Gemini.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Convert to mp3 if it's not already, to ensure compatibility and optimization
    try:
        if path.suffix.lower() != ".mp3":
            print(f"Converting {audio_path} to mp3...")
            audio = AudioSegment.from_file(audio_path)
            output_path = path.with_suffix(".mp3")
            audio.export(output_path, format="mp3")
            upload_path = output_path
        else:
            upload_path = path

        processor = FileProcessor(client)
        uploaded_file = processor.upload_file(str(upload_path))
        return processor.wait_for_processing(uploaded_file.name)
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        # If conversion fails, try uploading original
        print("Attempting to upload original file...")
        processor = FileProcessor(client)
        uploaded_file = processor.upload_file(str(path))
        return processor.wait_for_processing(uploaded_file.name)

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

def generate_audio(client: genai.Client, text: str, output_file: str = "output.wav") -> str:
    """
    Generates audio from text using Gemini TTS.
    """
    try:
        response = client.models.generate_content(
           model="gemini-2.5-flash-preview-tts",
           contents=f"Say: {text}",
           config=types.GenerateContentConfig(
              response_modalities=["AUDIO"],
              speech_config=types.SpeechConfig(
                 voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                       voice_name='Kore',
                    )
                 )
              ),
           )
        )
        
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if part.inline_data:
                data = part.inline_data.data
                wave_file(output_file, data)
                print(f"Generated audio saved to {output_file}")
                return output_file
            else:
                print("No inline audio data in response.")
        return None
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def add_citations(response: types.GenerateContentResponse) -> str:
    """
    Adds inline citations to the response text using grounding metadata.
    """
    if not response.candidates or not response.candidates[0].grounding_metadata:
        return response.text

    text = response.text
    grounding_metadata = response.candidates[0].grounding_metadata
    supports = grounding_metadata.grounding_supports
    chunks = grounding_metadata.grounding_chunks

    if not supports or not chunks:
        return text

    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    for support in sorted_supports:
        end_index = support.segment.end_index
        if support.grounding_chunk_indices:
            # Create citation string like [1](link1)[2](link2)
            citation_links = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].web.uri
                    citation_links.append(f"[{i + 1}]({uri})")

            citation_string = " " + " ".join(citation_links)
            text = text[:end_index] + citation_string + text[end_index:]

    return text
