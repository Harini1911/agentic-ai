"""
Basic audio demo for Gemini Live API.

Demonstrates:
- Simple audio streaming
- Session lifecycle management
- Real-time conversation
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import SessionManager, AudioHandler
from observability import initialize_tracing

load_dotenv()


async def main():
    """Run basic audio demo."""
    print("🎙️  Basic Audio Demo - Gemini Live API")
    print("=" * 50)
    print("This demo shows basic audio streaming with Gemini.")
    print("Speak into your microphone to interact!")
    print("Press Ctrl+C to exit.")
    print("=" * 50)
    
    # Initialize tracing
    tracer = initialize_tracing()
    session_id = str(uuid.uuid4())
    
    # Initialize Gemini client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
    
    # Create session manager and audio handler
    session = SessionManager(
        client=client,
        model=model,
        config={
            "system_instruction": "You are a helpful and friendly AI assistant. Keep responses concise and natural.",
        },
        on_state_change=lambda state: print(f"📡 Session state: {state.value}")
    )
    
    audio = AudioHandler()
    
    try:
        # Start session with tracing
        with tracer.trace_session(session_id, {"demo": "basic_audio"}):
            async with session, audio:
                print("\n✅ Connected! Start speaking...")
                
                # Task 1: Capture audio from mic and send to Gemini
                async def send_audio():
                    # Start capture loop in background
                    asyncio.create_task(audio.capture_audio_loop())
                    while True:
                        audio_chunk = await audio.get_input_audio()
                        await session.send_audio(
                            audio_chunk["data"],
                            audio_chunk["mime_type"]
                        )
                
                # Task 2: Receive responses from Gemini and play
                async def receive_audio():
                    turn_number = 0
                    while True:
                        turn_number += 1
                        
                        with tracer.trace_turn(turn_number):
                            async for response in session.receive():
                                # Handle audio output
                                if response.data is not None:
                                    await audio.queue_output_audio(response.data)
                                
                                # Handle interruptions
                                if (response.server_content and 
                                    response.server_content.interrupted):
                                    print("\n🔄 Interrupted by user")
                                    audio.clear_output_queue()
                                    tracer.track_interruption()
                                    # Resume normal operation after interruption
                                    session.resume()
                
                # Start all tasks concurrently (Python 3.10 compatible)
                await asyncio.gather(
                    send_audio(),
                    receive_audio(),
                    audio.playback_audio_loop(),
                )
                    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        tracer.track_error(e, "main_loop")


if __name__ == "__main__":
    asyncio.run(main())
