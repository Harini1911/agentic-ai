"""
FastAPI server for ephemeral token generation.

This server provides secure token generation for client-side access to Gemini Live API.
It never exposes the API key to clients, only short-lived ephemeral tokens.
"""

import datetime
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google import genai
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI(title="Live AI Assistant Token Server")

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
    api_key=os.getenv("GOOGLE_API_KEY"),  # Changed from GEMINI_API_KEY
    http_options={"api_version": "v1alpha"},
)

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


@app.get("/")
async def root():
    """Serve the web client."""
    return FileResponse(CLIENT_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Token server is running"
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
        new_session_expire_time = now + datetime.timedelta(minutes=1)
        
        token = client.auth_tokens.create(
            config={
                "uses": 1,  # Single session per token
                "expire_time": expire_time,
                "new_session_expire_time": new_session_expire_time,
                "live_connect_constraints": {
                    "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025"),
                    "config": {
                        "session_resumption": {},
                        "response_modalities": ["AUDIO"],
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


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "localhost")
    port = int(os.getenv("SERVER_PORT", 8000))
    
    print(f"🚀 Starting token server on http://{host}:{port}")
    print(f"📝 API docs available at http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)
