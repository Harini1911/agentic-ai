"""
FastAPI server for ephemeral token generation and WebSocket proxy.

This server provides secure token generation for client-side access to Gemini Live API
and WebSocket proxy for browser-based real-time communication.
"""

import datetime
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google import genai
from pydantic import BaseModel
import websockets

# Load environment variables first
load_dotenv()

# Import WebSocket proxy - must be after load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we can import from the parent directory
from websocket_proxy import WebSocketProxyServer


app = FastAPI(title="Live AI Assistant Server")

# Configure CORS for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options={"api_version": "v1alpha"},
)

# Initialize WebSocket proxy server
ws_proxy = WebSocketProxyServer()

# Token cache to reuse valid tokens
_token_cache: Optional[dict] = None

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_DIR = BASE_DIR / "client"


class TokenResponse(BaseModel):
    """Response model for token endpoint."""
    token: str
    expires_at: str
    new_session_expires_at: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    active_sessions: int
    sessions: list


@app.get("/")
async def root():
    """Serve the web client."""
    return FileResponse(CLIENT_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Live AI Assistant server is running"
    )


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get metrics for all active sessions."""
    sessions = ws_proxy.get_all_metrics()
    return MetricsResponse(
        active_sessions=len(sessions),
        sessions=sessions
    )


@app.post("/api/token", response_model=TokenResponse)
async def generate_token():
    """
    Generate an ephemeral token for Live API access.
    
    This endpoint creates a short-lived token that clients can use to connect
    to the Gemini Live API without exposing the API key.
    
    Returns:
        TokenResponse with token and expiration times
    """
    global _token_cache
    
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        
        # Check if we have a valid cached token
        if _token_cache and _token_cache["new_session_expires_at"] > now:
            return TokenResponse(
                token=_token_cache["token"],
                expires_at=_token_cache["expires_at"].isoformat(),
                new_session_expires_at=_token_cache["new_session_expires_at"].isoformat(),
            )
        
        # Generate new token
        expire_time = now + datetime.timedelta(minutes=30)
        new_session_expire_time = now + datetime.timedelta(minutes=5)
        
        token = client.auth_tokens.create(
            config={
                "uses": 10,  # Multiple sessions per token for web app
                "expire_time": expire_time,
                "new_session_expire_time": new_session_expire_time,
                "live_connect_constraints": {
                    "model": os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-native-audio-preview-12-2025"),
                    "config": {
                        "session_resumption": {}
                    },
                },
                "http_options": {"api_version": "v1alpha"},
            }
        )
        
        # Cache the token
        _token_cache = {
            "token": token.name,
            "expires_at": expire_time,
            "new_session_expires_at": new_session_expire_time,
        }
        
        return TokenResponse(
            token=token.name,
            expires_at=expire_time.isoformat(),
            new_session_expires_at=new_session_expire_time.isoformat(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate token: {str(e)}"
        )


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for browser clients to connect to Gemini Live API.
    
    This endpoint proxies WebSocket connections to the Gemini Live API,
    handling audio streaming, tool execution, and session management.
    """
    await websocket.accept()
    await ws_proxy.handle_client(websocket, "/ws/live")


# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=CLIENT_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "localhost")
    port = int(os.getenv("SERVER_PORT", 8000))
    
    print(f"🚀 Starting Live AI Assistant server on http://{host}:{port}")
    print(f"📝 API docs available at http://{host}:{port}/docs")
    print(f"🌐 Web app available at http://{host}:{port}")
    print(f"🔌 WebSocket endpoint: ws://{host}:{port}/ws/live")
    
    uvicorn.run(app, host=host, port=port)

