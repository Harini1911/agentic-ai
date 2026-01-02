"""
WebSocket proxy server for browser-to-Gemini Live API communication.

This proxy bridges browser WebSocket connections to the Gemini Live API,
handling audio streaming, tool execution, and session management.
"""

import asyncio
import json
import uuid
from typing import Dict, Optional
from datetime import datetime

from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# Import core components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import SessionManager
from tools import ToolExecutor, get_weather, get_forecast
from tools.datetime_tool import get_current_time, get_time_difference
from tools.search_tool import GOOGLE_SEARCH_TOOL
from observability import get_tracer

load_dotenv()


class LiveSession:
    """
    Manages a single live session for a browser client.
    
    Handles audio streaming, tool execution, and state management.
    """
    
    def __init__(self, session_id: str, websocket):
        self.session_id = session_id
        self.websocket = websocket
        self.gemini_session: Optional[SessionManager] = None
        self.tool_executor = ToolExecutor()
        self.tracer = get_tracer()
        self.is_active = False
        
        # Setup tools
        self._setup_tools()
        
        # Metrics
        self.turn_count = 0
        self.tool_calls_count = 0
        self.start_time = datetime.now()
    
    def _setup_tools(self):
        """Register all available tools."""
        # Weather tools
        self.tool_executor.register_tool(
            name="get_weather",
            description="Get current weather conditions for a specific city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        )(get_weather)
        
        self.tool_executor.register_tool(
            name="get_forecast",
            description="Get 7-day weather forecast for a city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        )(get_forecast)
        
        # DateTime tools
        self.tool_executor.register_tool(
            name="get_current_time",
            description="Get current time in a specific timezone",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name (e.g., 'America/New_York', 'Asia/Tokyo')"
                    }
                },
                "required": []
            }
        )(get_current_time)
        
        self.tool_executor.register_tool(
            name="get_time_difference",
            description="Calculate time difference between two timezones",
            parameters={
                "type": "object",
                "properties": {
                    "timezone1": {"type": "string"},
                    "timezone2": {"type": "string"}
                },
                "required": ["timezone1", "timezone2"]
            }
        )(get_time_difference)
    
    async def connect(self):
        """Connect to Gemini Live API."""
        try:
            print(f"🔄 Connecting session {self.session_id}...")
            
            # Initialize Gemini client
            client = genai.Client(
                api_key=os.getenv("GOOGLE_API_KEY"),
                http_options={"api_version": "v1alpha"}
            )
            
            model = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-native-audio-preview-12-2025")
            print(f"📡 Using model: {model}")
            
            # Prepare tools configuration
            tools = [
                GOOGLE_SEARCH_TOOL,
                *self.tool_executor.get_tool_declarations()
            ]
            
            # Create session with simplified config
            # Note: response_modalities is not needed for native audio models
            self.gemini_session = SessionManager(
                client=client,
                model=model,
                config={
                    "system_instruction": "You are a helpful AI assistant with access to real-time information. Use tools when needed to provide accurate, up-to-date information. Keep responses natural and conversational.",
                    "tools": tools
                },
                on_state_change=self._on_state_change
            )
            
            print(f"🔌 Connecting to Gemini Live API...")
            await self.gemini_session.connect()
            self.is_active = True
            print(f"✅ Session {self.session_id} connected successfully!")
            
            # Send connection success to client
            await self._send_to_client({
                "type": "connected",
                "session_id": self.session_id,
                "state": "connected"
            })
            
            # Start receiving responses
            asyncio.create_task(self._receive_loop())
            
        except Exception as e:
            print(f"❌ Connection error for session {self.session_id}: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            await self._send_to_client({
                "type": "error",
                "error": f"Connection failed: {str(e)}"
            })
            raise
    
    async def disconnect(self):
        """Disconnect from Gemini Live API."""
        self.is_active = False
        if self.gemini_session:
            await self.gemini_session.disconnect()
        
        await self._send_to_client({
            "type": "disconnected",
            "session_id": self.session_id
        })
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to Gemini."""
        if self.gemini_session and self.is_active:
            await self.gemini_session.send_audio(audio_data, "audio/pcm")
    
    async def send_text(self, text: str):
        """Send text message to Gemini."""
        if self.gemini_session and self.is_active:
            await self.gemini_session.send_text(text)
    
    async def reset_session(self):
        """Reset the session."""
        if self.gemini_session:
            await self.gemini_session.reset()
            self.turn_count = 0
            self.tool_calls_count = 0
            
            await self._send_to_client({
                "type": "session_reset",
                "session_id": self.session_id
            })
    
    async def _receive_loop(self):
        """Receive and process responses from Gemini."""
        try:
            while self.is_active and self.gemini_session:
                self.turn_count += 1
                
                async for response in self.gemini_session.receive():
                    # Handle audio output
                    if response.data is not None:
                        await self._send_to_client({
                            "type": "audio",
                            "data": response.data.hex()  # Convert bytes to hex string
                        })
                    
                    # Handle text output
                    if response.server_content and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if part.text:
                                await self._send_to_client({
                                    "type": "text",
                                    "text": part.text
                                })
                    
                    # Handle tool calls
                    if response.tool_call:
                        await self._handle_tool_calls(response.tool_call)
                    
                    # Handle interruptions
                    if response.server_content and response.server_content.interrupted:
                        await self._send_to_client({
                            "type": "interrupted"
                        })
                        self.gemini_session.resume()
                    
                    # Handle turn completion
                    if response.server_content and response.server_content.turn_complete:
                        await self._send_to_client({
                            "type": "turn_complete",
                            "turn_number": self.turn_count
                        })
                        break
                        
        except Exception as e:
            await self._send_to_client({
                "type": "error",
                "error": f"Receive loop error: {str(e)}"
            })
    
    async def _handle_tool_calls(self, tool_call):
        """Execute tool calls and send results back."""
        try:
            function_calls = tool_call.function_calls
            
            # Notify client about tool execution
            await self._send_to_client({
                "type": "tool_call_start",
                "tools": [
                    {
                        "name": fc.name,
                        "args": fc.args or {}
                    }
                    for fc in function_calls
                ]
            })
            
            # Execute tools
            results = []
            for fc in function_calls:
                self.tool_calls_count += 1
                
                with self.tracer.trace_tool_call(fc.name, fc.args or {}):
                    result = await self.tool_executor.execute_tool(fc)
                    results.append(result)
                    
                    # Send result to client
                    await self._send_to_client({
                        "type": "tool_result",
                        "tool": fc.name,
                        "result": result.response
                    })
            
            # Send results back to Gemini
            await self.gemini_session.send_tool_response(results)
            
        except Exception as e:
            await self._send_to_client({
                "type": "error",
                "error": f"Tool execution error: {str(e)}"
            })
    
    def _on_state_change(self, state):
        """Handle session state changes."""
        asyncio.create_task(self._send_to_client({
            "type": "state_change",
            "state": state.value
        }))
    
    async def _send_to_client(self, message: dict):
        """Send message to browser client."""
        try:
            # Check if WebSocket is still open before sending
            if not self.websocket.client_state.name == "CONNECTED":
                return
            
            # FastAPI/Starlette WebSocket handles JSON serialization automatically
            # Just send the dict directly
            await self.websocket.send_json(message)
        except Exception as e:
            # Silently ignore errors if connection is already closed
            if "websocket.close" not in str(e).lower():
                print(f"Error sending to client {self.session_id}: {type(e).__name__}: {e}")
    
    def get_metrics(self) -> dict:
        """Get session metrics."""
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "session_id": self.session_id,
            "duration_seconds": duration,
            "turn_count": self.turn_count,
            "tool_calls_count": self.tool_calls_count,
            "state": self.gemini_session.state.value if self.gemini_session else "disconnected"
        }


class WebSocketProxyServer:
    """
    WebSocket proxy server managing multiple browser sessions.
    """
    
    def __init__(self):
        self.sessions: Dict[str, LiveSession] = {}
    
    async def handle_client(self, websocket, path):
        """Handle a new WebSocket connection from a browser client."""
        session_id = str(uuid.uuid4())
        session = LiveSession(session_id, websocket)
        self.sessions[session_id] = session
        
        print(f"✅ New client connected: {session_id}")
        
        try:
            # Connect to Gemini
            await session.connect()
            
            # Handle incoming messages
            while True:
                try:
                    # Receive message from WebSocket
                    data = await websocket.receive_text()
                    
                    try:
                        message = json.loads(data)
                        await self._handle_message(session, message)
                    except json.JSONDecodeError:
                        # Assume it's raw audio data in hex format
                        await session.send_audio(bytes.fromhex(data))
                except Exception as e:
                    print(f"Error handling message: {e}")
                    break
                    
        except Exception as e:
            print(f"Client error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            await session.disconnect()
            del self.sessions[session_id]
            print(f"❌ Client disconnected: {session_id}")
    
    async def _handle_message(self, session: LiveSession, data: dict):
        """Handle different message types from client."""
        msg_type = data.get("type")
        
        if msg_type == "audio":
            # Audio data in hex format
            audio_bytes = bytes.fromhex(data["data"])
            await session.send_audio(audio_bytes)
        
        elif msg_type == "text":
            await session.send_text(data["text"])
        
        elif msg_type == "reset":
            await session.reset_session()
        
        elif msg_type == "ping":
            await session._send_to_client({"type": "pong"})
    
    def get_all_metrics(self) -> list:
        """Get metrics for all active sessions."""
        return [session.get_metrics() for session in self.sessions.values()]
