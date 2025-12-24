# How to Run the Web Client

## Quick Start

1. **Start the backend server:**
   ```bash
   cd /4TBHD/harini/agentic-ai/live-api
   uv run python3 server/server.py
   ```

2. **Open in your browser:**
   - Local: http://localhost:8000
   - Remote: http://YOUR_SERVER_IP:8000

3. **Click "Connect" and allow microphone access**

4. **Start speaking!** The AI will respond with audio.

## Architecture

```
Your Laptop Browser          Remote Server
┌──────────────┐            ┌──────────────┐
│              │            │              │
│  Web Client  │───────────▶│   FastAPI    │
│ (index.html) │  HTTPS     │   Server     │
│              │            │              │
│  - Mic/Audio │            │  - Tokens    │
│  - WebSocket │            │  - API Keys  │
└──────┬───────┘            └──────────────┘
       │
       │ WebSocket
       ▼
┌──────────────┐
│    Gemini    │
│   Live API   │
└──────────────┘
```

## Features

- ✅ Real-time voice interaction
- ✅ Secure ephemeral tokens
- ✅ Beautiful UI with status indicators
- ✅ Activity logs
- ✅ Works on any device with a browser

## Troubleshooting

### "Token fetch failed"
- Make sure the server is running
- Check that `.env` has `GOOGLE_API_KEY` set

### "Microphone access denied"
- Click the browser's permission prompt
- Check browser settings for microphone access

### "Connection failed"
- Ensure your firewall allows port 8000
- Try using `0.0.0.0` instead of `localhost` in server config

## Security Notes

- API keys stay on the server (never exposed to browser)
- Tokens expire after 30 minutes
- Each token can only be used once
- HTTPS recommended for production
