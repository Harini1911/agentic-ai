"""
Session manager for Gemini Live API.

Handles WebSocket connection lifecycle, session state, interruptions,
and session resumption for long-running conversations.
"""

import asyncio
from enum import Enum
from typing import Optional, AsyncIterator, Callable
from google import genai
from google.genai import types


class SessionState(Enum):
    """Session state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    INTERRUPTED = "interrupted"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class SessionManager:
    """
    Manages Live API session lifecycle and state.
    
    Features:
    - WebSocket connection management
    - Session state tracking
    - Interruption handling
    - Session resumption support
    - Context window compression for long conversations
    """
    
    def __init__(
        self,
        client: genai.Client,
        model: str,
        config: Optional[dict] = None,
        on_state_change: Optional[Callable[[SessionState], None]] = None,
    ):
        """
        Initialize session manager.
        
        Args:
            client: Gemini client instance
            model: Model name to use
            config: Optional session configuration
            on_state_change: Optional callback for state changes
        """
        self.client = client
        self.model = model
        self.config = config or {}
        self.on_state_change = on_state_change
        
        self._state = SessionState.DISCONNECTED
        self._session: Optional[genai.LiveConnectSession] = None
        self._session_context = None  # Store the context manager
        self._resumption_token: Optional[str] = None
        self._conversation_history: list = []
        
    @property
    def state(self) -> SessionState:
        """Get current session state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if session is connected."""
        return self._state == SessionState.CONNECTED
    
    def _set_state(self, new_state: SessionState):
        """Update session state and trigger callback."""
        if self._state != new_state:
            self._state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)
    
    async def connect(self) -> bool:
        """
        Establish connection to Live API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._set_state(SessionState.CONNECTING)
            
            # Prepare configuration with session resumption
            session_config = {
                "response_modalities": ["AUDIO"],
                "session_resumption": {},  # Enable session resumption
                **self.config,
            }
            
            # Connect to Live API - store the context manager
            self._session_context = self.client.aio.live.connect(
                model=self.model,
                config=session_config,
            )
            
            # Enter the context manager
            self._session = await self._session_context.__aenter__()
            
            self._set_state(SessionState.CONNECTED)
            return True
            
        except Exception as e:
            self._set_state(SessionState.ERROR)
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Gracefully disconnect from Live API."""
        if self._session and hasattr(self, '_session_context'):
            try:
                self._set_state(SessionState.CLOSING)
                # Properly exit the context manager
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️  Error during disconnect: {e}")
            finally:
                self._session = None
                self._session_context = None
                self._set_state(SessionState.CLOSED)
    
    async def send_text(self, text: str):
        """
        Send text message to the model.
        
        Args:
            text: Text message to send
        """
        if not self.is_connected or not self._session:
            raise RuntimeError("Session not connected")
        
        await self._session.send_client_content(
            turns={"parts": [{"text": text}]}
        )
        
        # Track in conversation history
        self._conversation_history.append({
            "role": "user",
            "content": text,
            "type": "text"
        })
    
    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm"):
        """
        Send audio data to the model.
        
        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type of audio data
        """
        if not self.is_connected or not self._session:
            raise RuntimeError("Session not connected")
        
        await self._session.send_realtime_input(
            audio={"data": audio_data, "mime_type": mime_type}
        )
    
    async def send_tool_response(self, function_responses: list):
        """
        Send tool execution results back to the model.
        
        Args:
            function_responses: List of FunctionResponse objects
        """
        if not self.is_connected or not self._session:
            raise RuntimeError("Session not connected")
        
        await self._session.send_tool_response(
            function_responses=function_responses
        )
    
    async def receive(self) -> AsyncIterator:
        """
        Receive responses from the model.
        
        Yields:
            Response chunks from the Live API
        """
        # Allow receiving in both CONNECTED and INTERRUPTED states
        # Interruptions are part of normal conversation flow
        if self._state not in (SessionState.CONNECTED, SessionState.INTERRUPTED) or not self._session:
            raise RuntimeError("Session not connected")
        
        turn = self._session.receive()
        async for response in turn:
            # Check for interruption
            if (response.server_content and 
                response.server_content.interrupted):
                self._set_state(SessionState.INTERRUPTED)
            
            # Check for session resumption updates
            if hasattr(response, 'session_resumption_update') and response.session_resumption_update:
                # Safely access the token attribute if it exists
                if hasattr(response.session_resumption_update, 'token'):
                    self._resumption_token = response.session_resumption_update.token
                # Some versions might use 'resumption_token' instead
                elif hasattr(response.session_resumption_update, 'resumption_token'):
                    self._resumption_token = response.session_resumption_update.resumption_token
            
            yield response
    
    def resume(self):
        """
        Resume normal operation after an interruption.
        
        This resets the state from INTERRUPTED back to CONNECTED,
        allowing the conversation to continue normally.
        """
        if self._state == SessionState.INTERRUPTED:
            self._set_state(SessionState.CONNECTED)
    
    async def reset(self):
        """
        Reset the session (clear conversation history).
        
        This closes the current session and starts a new one.
        """
        await self.disconnect()
        self._conversation_history.clear()
        self._resumption_token = None
        await self.connect()
    
    def get_conversation_history(self) -> list:
        """Get conversation history."""
        return self._conversation_history.copy()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
