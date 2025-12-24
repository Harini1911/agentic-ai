"""
Session management demo for Gemini Live API - Python 3.10 compatible.

Demonstrates:
- Session interruption handling
- Session reset (clear context)
- Multi-turn conversations
- Context preservation
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
    """Run session management demo."""
    print("🔄 Session Management Demo - Gemini Live API")
    print("=" * 50)
    print("This demo shows session management features:")
    print("- Multi-turn conversations with context")
    print("- Interruption handling (barge-in)")
    print("- Session reset")
    print("\nCommands:")
    print("  Type 'reset' to clear conversation history")
    print("  Press Ctrl+C to exit")
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
            "system_instruction": "You are a helpful AI assistant. Remember context from previous turns in the conversation.",
        },
        on_state_change=lambda state: print(f"📡 Session state: {state.value}")
    )
    
    audio = AudioHandler()
    
    # Command queue for session control
    command_queue = asyncio.Queue()
    
    async def command_listener():
        """Listen for text commands."""
        while True:
            try:
                # In a real implementation, this would read from stdin
                # For demo purposes, we'll just wait
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Command listener error: {e}")
    
    try:
        # Start session with tracing
        with tracer.trace_session(session_id, {"demo": "session_management"}):
            async with session, audio:
                print("\n✅ Connected! Have a multi-turn conversation...")
                print("💡 Try asking follow-up questions to test context preservation")
                
                turn_count = 0
                
                # Task 1: Capture and send audio
                async def send_audio():
                    asyncio.create_task(audio.capture_audio_loop())
                    while True:
                        audio_chunk = await audio.get_input_audio()
                        await session.send_audio(
                            audio_chunk["data"],
                            audio_chunk["mime_type"]
                        )
                
                # Task 2: Receive responses
                async def receive_audio():
                    nonlocal turn_count
                    
                    while True:
                        turn_count += 1
                        
                        with tracer.trace_turn(turn_count):
                            print(f"\n--- Turn {turn_count} ---")
                            
                            async for response in session.receive():
                                # Handle audio output
                                if response.data is not None:
                                    await audio.queue_output_audio(response.data)
                                
                                # Handle interruptions
                                if (response.server_content and 
                                    response.server_content.interrupted):
                                    print("🔄 Interrupted! You can speak now.")
                                    audio.clear_output_queue()
                                    tracer.track_interruption()
                            
                            # Show conversation history
                            history = session.get_conversation_history()
                            print(f"📝 Conversation has {len(history)} turns")
                
                # Task 3: Handle session commands
                async def handle_commands():
                    while True:
                        try:
                            command = await command_queue.get()
                            
                            if command == "reset":
                                print("\n🔄 Resetting session...")
                                await session.reset()
                                print("✅ Session reset! Context cleared.")
                                
                        except Exception as e:
                            print(f"Command error: {e}")
                
                # Start all tasks concurrently (Python 3.10 compatible)
                await asyncio.gather(
                    send_audio(),
                    receive_audio(),
                    audio.playback_audio_loop(),
                    handle_commands(),
                    command_listener(),
                )
                    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        print(f"📊 Total turns: {turn_count}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        tracer.track_error(e, "main_loop")


if __name__ == "__main__":
    asyncio.run(main())
