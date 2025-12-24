"""
Tool calling demo for Gemini Live API - Python 3.10 compatible.

Demonstrates:
- Google Search integration
- Weather API tool calling
- Tool execution flow
- Real-time tool invocation
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
from tools import ToolExecutor, get_weather, get_forecast, GOOGLE_SEARCH_TOOL
from tools.search_tool import parse_search_results, format_search_summary
from observability import initialize_tracing

load_dotenv()


async def main():
    """Run tool calling demo."""
    print("🔧 Tool Calling Demo - Gemini Live API")
    print("=" * 50)
    print("This demo shows real-time tool invocation:")
    print("- Google Search for current information")
    print("- Weather API for location-based data")
    print("\nTry asking:")
    print("  - 'What's the weather in London?'")
    print("  - 'When did the last Olympics happen?'")
    print("\nPress Ctrl+C to exit.")
    print("=" * 50)
    
    # Initialize tracing
    tracer = initialize_tracing()
    session_id = str(uuid.uuid4())
    
    # Initialize Gemini client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
    
    # Set up tool executor
    tool_executor = ToolExecutor()
    
    # Register weather tools
    tool_executor.register_tool(
        name="get_weather",
        description="Get current weather conditions for a specific city",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    )(get_weather)
    
    tool_executor.register_tool(
        name="get_forecast",
        description="Get 7-day weather forecast for a city",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    )(get_forecast)
    
    # Prepare tools configuration
    tools = [
        GOOGLE_SEARCH_TOOL,  # Google Search grounding
        *tool_executor.get_tool_declarations(),  # Weather tools
    ]
    
    # Create session manager and audio handler
    session = SessionManager(
        client=client,
        model=model,
        config={
            "system_instruction": "You are a helpful AI assistant with access to real-time information via Google Search and weather data. Use these tools when needed to provide accurate, up-to-date information.",
            "tools": tools,
        },
        on_state_change=lambda state: print(f"📡 Session state: {state.value}")
    )
    
    audio = AudioHandler()
    
    try:
        # Start session with tracing
        with tracer.trace_session(session_id, {"demo": "tool_calling"}):
            async with session, audio:
                print("\n✅ Connected! Ask me about weather or current events...")
                
                # Task 1: Capture and send audio
                async def send_audio():
                    asyncio.create_task(audio.capture_audio_loop())
                    while True:
                        audio_chunk = await audio.get_input_audio()
                        await session.send_audio(
                            audio_chunk["data"],
                            audio_chunk["mime_type"]
                        )
                
                # Task 2: Receive responses and handle tools
                async def receive_and_process():
                    turn_number = 0
                    while True:
                        turn_number += 1
                        
                        with tracer.trace_turn(turn_number):
                            async for response in session.receive():
                                # Handle audio output
                                if response.data is not None:
                                    await audio.queue_output_audio(response.data)
                                
                                # Handle Google Search results
                                search_results = parse_search_results(response)
                                if search_results["search_performed"]:
                                    print("\n" + format_search_summary(search_results))
                                
                                # Handle function calls (weather tools)
                                if response.tool_call:
                                    print(f"\n🔧 Tool called: {len(response.tool_call.function_calls)} function(s)")
                                    
                                    # Execute tools
                                    function_responses = []
                                    for fc in response.tool_call.function_calls:
                                        print(f"   → {fc.name}({fc.args})")
                                        
                                        with tracer.trace_tool_call(fc.name, fc.args or {}):
                                            func_response = await tool_executor.execute_tool(fc)
                                            function_responses.append(func_response)
                                            print(f"   ✓ Result: {func_response.response}")
                                    
                                    # Send results back to model
                                    await session.send_tool_response(function_responses)
                                
                                # Handle interruptions
                                if (response.server_content and 
                                    response.server_content.interrupted):
                                    print("\n🔄 Interrupted by user")
                                    audio.clear_output_queue()
                                    tracer.track_interruption()
                
                # Start all tasks concurrently (Python 3.10 compatible)
                await asyncio.gather(
                    send_audio(),
                    receive_and_process(),
                    audio.playback_audio_loop(),
                )
                    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        tracer.track_error(e, "main_loop")


if __name__ == "__main__":
    asyncio.run(main())
