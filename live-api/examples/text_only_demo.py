"""
Simple text-only demo for Gemini Live API (no audio required).

Demonstrates:
- Text-based interaction with Live API
- Session lifecycle management
- Tool calling with weather
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

from core import SessionManager
from tools import ToolExecutor, get_weather, GOOGLE_SEARCH_TOOL
from observability import initialize_tracing

load_dotenv()


async def main():
    """Run text-only demo."""
    print("💬 Text-Only Demo - Gemini Live API")
    print("=" * 50)
    print("This demo shows text-based interaction (no audio).")
    print("Testing session management and tool calling.")
    print("=" * 50)
    
    # Initialize tracing
    tracer = initialize_tracing()
    session_id = str(uuid.uuid4())
    
    # Initialize Gemini client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
    
    # Set up tool executor
    tool_executor = ToolExecutor()
    
    # Register weather tool
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
    
    # Prepare tools configuration
    tools = [
        GOOGLE_SEARCH_TOOL,
        *tool_executor.get_tool_declarations(),
    ]
    
    # Create session manager
    session = SessionManager(
        client=client,
        model=model,
        config={
            "system_instruction": "You are a helpful AI assistant. Keep responses concise.",
            "tools": tools,
            "response_modalities": ["TEXT"],  # Text-only mode
        },
        on_state_change=lambda state: print(f"📡 Session state: {state.value}")
    )
    
    try:
        # Start session with tracing
        with tracer.trace_session(session_id, {"demo": "text_only"}):
            async with session:
                print("\n✅ Connected! Sending test messages...\n")
                
                # Test 1: Simple greeting
                print("Test 1: Simple greeting")
                print("User: Hello!")
                await session.send_text("Hello!")
                
                async for response in session.receive():
                    if response.server_content and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if part.text:
                                print(f"Assistant: {part.text}")
                        break  # Move to next test
                
                print("\n" + "-" * 50 + "\n")
                
                # Test 2: Weather query (tool calling)
                print("Test 2: Weather query (tool calling)")
                print("User: What's the weather in Paris?")
                await session.send_text("What's the weather in Paris?")
                
                async for response in session.receive():
                    # Handle tool calls
                    if response.tool_call:
                        print(f"🔧 Tool called: {response.tool_call.function_calls[0].name}")
                        
                        # Execute tool
                        func_responses = []
                        for fc in response.tool_call.function_calls:
                            result = await tool_executor.execute_tool(fc)
                            func_responses.append(result)
                            print(f"   Result: {result.response}")
                        
                        # Send results back
                        await session.send_tool_response(func_responses)
                    
                    # Handle text response
                    if response.server_content and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if part.text:
                                print(f"Assistant: {part.text}")
                        
                        # Check if turn is complete
                        if response.server_content.turn_complete:
                            break
                
                print("\n" + "-" * 50 + "\n")
                print("✅ All tests completed successfully!")
                    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        tracer.track_error(e, "main_loop")


if __name__ == "__main__":
    asyncio.run(main())
