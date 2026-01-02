# Real-Time Live AI Assistant

A production-ready implementation of a real-time AI assistant using the **Gemini Live API**. This project demonstrates deep understanding of live, streaming, multimodal AI systems with comprehensive observability and security.


---

## Project Structure

```
live-api/
├── server/
│   └── server.py              # Ephemeral token generation server
├── core/
│   ├── session_manager.py     # Session lifecycle management
│   └── audio_handler.py       # Real-time audio I/O
├── tools/
│   ├── tool_executor.py       # Tool orchestration
│   ├── weather_tool.py        # Weather API integration
│   └── search_tool.py         # Google Search utilities
├── observability/
│   └── laminar_tracer.py      # Laminar tracing integration
├── examples/
│   ├── basic_audio_demo.py    # Simple audio streaming
│   ├── tool_calling_demo.py   # Tool invocation demo
│   └── session_management_demo.py  # Session handling demo
├── docs/
│   └── CONCEPTS.md            # Deep conceptual documentation
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── .env.example               # Environment variable template
├── pyproject.toml             # Dependencies
└── README.md                  # This file
```

## Features

- **Real-Time Audio Streaming**: Bidirectional audio with low latency (<2s)
- **Live Tool Invocation**: Google Search and Weather API integration
- **Secure Token Management**: Ephemeral tokens for client-side access
- **Session Management**: Context preservation, interruption handling, resumption
- **Comprehensive Observability**: Laminar integration for tracing and debugging
- **Production-Ready**: Error handling, logging, and best practices

---



## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │◄───────►│    Backend   │◄───────►│   Gemini    │
│  (Browser)  │  HTTPS  │    Server    │  HTTPS  │  Live API   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                         │
      │ 1. Request Token       │                         │
      ├───────────────────────►│                         │
      │                        │ 2. Create Ephemeral     │
      │                        ├────────────────────────►│
      │                        │ 3. Return Token         │
      │                        │◄────────────────────────┤
      │ 4. Return Token        │                         │
      │◄───────────────────────┤                         │
      │                        │                         │
      │ 5. Connect WebSocket (with token)                │
      ├─────────────────────────────────────────────────►│
      │                        │                         │
      │ 6. Stream Audio ◄───────────────────────────────►│
      │                        │                         │
      │                        │ 7. Laminar Tracing      │
      │                        ├────────────────────────►│
      │                        │                      Laminar
```

### Components

- **`server/`**: FastAPI backend for ephemeral token generation
- **`core/`**: Session management and audio handling
- **`tools/`**: Tool executor and integrations (Search, Weather)
- **`observability/`**: Laminar tracing for debugging
- **`examples/`**: Demo scripts showing various features

---

## Quick Start

### Prerequisites

- Python 3.10+
- Google AI API key ([Get one here](https://aistudio.google.com/apikey))
- Laminar API key ([Sign up](https://www.lmnr.ai/))
- System audio dependencies:
  - **macOS**: `brew install portaudio`
  - **Linux**: `sudo apt-get install portaudio19-dev`
  - **Windows**: Download from [PyAudio website](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

**Note**: Weather data uses Open-Meteo API (free, no API key required)

### Installation

1. **Clone the repository**:
   ```bash
   cd live-api
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required variables:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   LAMINAR_PROJECT_API_KEY=your_laminar_key_here
   ```

### Quick Start - Web Client (Recommended)

```bash
# Start the server
uv run python3 server/server.py

# Open http://localhost:8000 in your browser
# Click "Connect" and allow microphone access
# Start speaking!
```

### Quick Start - CLI Demos (Requires Audio Hardware)

**Basic Audio Demo** (Simple conversation):
```bash
cd live-api
uv run python3 examples/basic_audio_demo.py
```

**Tool Calling Demo** (Google Search + Weather):
```bash
uv run python3 examples/tool_calling_demo.py
```

**Session Management Demo** (Multi-turn conversations):
```bash
uv run python3 examples/session_management_demo.py
```

### Run Web Interface

**Start the server:**
```bash
cd live-api
uv run python3 server/server.py
```

**Access the dashboard:**
- Local: http://localhost:8000
- Remote: http://YOUR_SERVER_IP:8000

**What's Available:**
- API documentation at `/docs`
- Token generation endpoint `/api/token`
- Health check endpoint `/health`
- Information dashboard

**Note on Browser Client:**
The Gemini Live API's ephemeral tokens are designed for server-to-server or native app integration. For a full browser-based voice client, you would need to:
1. Use the official Google Generative AI JavaScript SDK
2. Implement a WebSocket proxy on the server
3. Or use the Python CLI demos on a machine with audio hardware

---

## Usage Examples


### Basic Audio Streaming

```python
from google import genai
from core import SessionManager, AudioHandler

client = genai.Client(api_key="your_api_key")

async with SessionManager(client, "gemini-2.5-flash-native-audio-preview-12-2025") as session:
    async with AudioHandler() as audio:
        # Send audio from microphone
        audio_chunk = await audio.get_input_audio()
        await session.send_audio(audio_chunk["data"], "audio/pcm")
        
        # Receive and play response
        async for response in session.receive():
            if response.data:
                await audio.queue_output_audio(response.data)
```

### Tool Calling

```python
from tools import ToolExecutor, get_weather

# Set up tool executor
executor = ToolExecutor()
executor.register_tool(
    name="get_weather",
    description="Get current weather",
    parameters={...}
)(get_weather)

# Use in session
config = {"tools": executor.get_tool_declarations()}
async with SessionManager(client, model, config=config) as session:
    async for response in session.receive():
        if response.tool_call:
            results = await executor.execute_multiple(response.tool_call.function_calls)
            await session.send_tool_response(function_responses=results)
```

### Ephemeral Token Server

```bash
# Start the token server
cd live-api
uv run python3 server/server.py
```

Access at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Generate token: `POST http://localhost:8000/api/token`

---

## Observability with Laminar

All demos automatically trace to Laminar for observability:

1. **Session Lifecycle**: Connection, disconnection, state changes
2. **Latency Metrics**: Per-turn response times
3. **Token Usage**: Input/output tokens per turn
4. **Tool Invocations**: Execution time and results
5. **Errors**: Automatic error capture with context

View traces at: [https://www.lmnr.ai/](https://www.lmnr.ai/)

---

## Testing

### Run Unit Tests

```bash
cd live-api
uv run pytest tests/unit -v
```

### Run Integration Tests

```bash
uv run pytest tests/integration -v
```

---

## Security Best Practices

1. **Never expose API keys**: Use ephemeral tokens for client-side access
2. **Short token lifetimes**: Default 30 minutes for active sessions
3. **Token constraints**: Lock tokens to specific models and configurations
4. **Rate limiting**: Limit token generation per user/IP
5. **Audit logging**: Track all token generation events

See [CONCEPTS.md](docs/CONCEPTS.md#5-ephemeral-tokens) for detailed security guidelines.

---

## Key Concepts

### Session States

- **DISCONNECTED**: No active connection
- **CONNECTING**: Establishing WebSocket
- **CONNECTED**: Active session
- **INTERRUPTED**: User spoke during response
- **CLOSING**: Gracefully shutting down
- **CLOSED**: Connection terminated

### Audio Formats

- **Input**: 16kHz, 16-bit, Mono PCM
- **Output**: 24kHz, 16-bit, Mono PCM

### Tool Calling Flow

1. User speaks → Model generates response
2. Model needs external data → Pauses generation
3. Model invokes tool → Client executes
4. Client sends result → Model resumes generation

---

## Troubleshooting

### Audio Issues

**No microphone input:**
```bash
# Check PyAudio installation
python -c "import pyaudio; print(pyaudio.PyAudio().get_default_input_device_info())"
```

**Audio playback issues:**
- Ensure no other applications are using audio device
- Check system audio settings
- Try different audio device indices

### Connection Issues

**WebSocket timeout:**
- Enable session resumption in config
- Check network connectivity
- Verify API key is valid

**Token expiration:**
- Implement proactive token renewal (5 min before expiry)
- Use session resumption for long conversations

### Tool Calling Issues

**Weather API errors:**
- Open-Meteo is free and requires no API key
- Ensure city name is spelled correctly
- Check internet connectivity

**Google Search not working:**
- Ensure `{"google_search": {}}` is in tools config
- Check model supports grounding (2.5 Flash and above)

---

