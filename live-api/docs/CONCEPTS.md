# Gemini Live API — Concepts & Architecture

This document provides deep conceptual understanding of the Gemini Live API, covering how it works internally, why design decisions were made, and common pitfalls to avoid.

---

## 1. Getting Started with Gemini Live API

### What It Is

The **Gemini Live API** is a real-time, bidirectional streaming API that enables low-latency voice and multimodal interactions with Gemini models. Unlike traditional request-response APIs where you send a complete prompt and wait for a complete response, Live API maintains a persistent connection and streams data in both directions simultaneously.

### How It Differs from Standard Request-Response APIs

| Feature | Standard API | Live API |
|---------|-------------|----------|
| **Connection** | One request → one response | Persistent WebSocket connection |
| **Latency** | Higher (wait for complete response) | Lower (streaming responses) |
| **Interaction** | Turn-based (sequential) | Real-time (simultaneous) |
| **Audio** | Pre-recorded files only | Live microphone input/output |
| **Interruption** | Not possible | Supported (barge-in) |
| **State** | Stateless | Stateful (maintains context) |

### Live Session Lifecycle

```
┌─────────────┐
│ DISCONNECTED│
└──────┬──────┘
       │ connect()
       ▼
┌─────────────┐
│ CONNECTING  │
└──────┬──────┘
       │ success
       ▼
┌─────────────┐     interrupt      ┌──────────────┐
│  CONNECTED  │◄──────────────────►│ INTERRUPTED  │
└──────┬──────┘                    └──────────────┘
       │ disconnect()
       ▼
┌─────────────┐
│   CLOSING   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   CLOSED    │
└─────────────┘
```

**States:**
- **DISCONNECTED**: No active connection
- **CONNECTING**: Establishing WebSocket connection
- **CONNECTED**: Active session, can exchange messages
- **INTERRUPTED**: User spoke while model was responding
- **CLOSING**: Gracefully shutting down
- **CLOSED**: Connection terminated

### Client ↔ Model Real-Time Interaction Flow

```
Client                          Gemini Live API
  │                                    │
  ├─── WebSocket Connect ─────────────►│
  │◄─── Connection Established ────────┤
  │                                    │
  ├─── Audio Stream (continuous) ─────►│
  │                                    │
  │◄─── Audio Response (streaming) ────┤
  │                                    │
  ├─── Audio Stream (interrupt) ──────►│
  │◄─── Previous response stopped ─────┤
  │◄─── New response starts ───────────┤
  │                                    │
  ├─── Tool Call Response ────────────►│
  │◄─── Continued generation ──────────┤
  │                                    │
  ├─── Disconnect ────────────────────►│
  │◄─── Connection Closed ─────────────┤
```

### Persistent vs Ephemeral Sessions

**Persistent Sessions:**
- Maintain conversation history across multiple turns
- Use context window compression to handle long conversations
- Support session resumption after brief disconnections
- Ideal for: Multi-turn conversations, customer support, interviews

**Ephemeral Sessions:**
- Single-turn interactions
- No context preservation
- Lower resource usage
- Ideal for: Quick queries, one-off tasks

### Common Pitfalls

1. **Not handling interruptions**: Users expect to interrupt AI responses. Always implement barge-in support.
2. **Ignoring connection limits**: WebSocket connections timeout after ~10 minutes. Use session resumption.
3. **Blocking audio queues**: Use bounded queues with proper backpressure to avoid memory issues.
4. **Forgetting context window limits**: Enable context compression for conversations longer than 10-15 turns.
5. **Exposing API keys**: Never send API keys to client-side code. Use ephemeral tokens.

---

## 2. Capabilities of Gemini Live API

### Streaming Text (Incremental Token Generation)

The model generates text incrementally, sending tokens as they're produced rather than waiting for the complete response.

**How it works:**
```python
async for response in session.receive():
    if response.server_content and response.server_content.model_turn:
        for part in response.server_content.model_turn.parts:
            if part.text:
                print(part.text, end='', flush=True)  # Incremental text
```

**Benefits:**
- Lower perceived latency (user sees response immediately)
- Better user experience (feels more natural)
- Can interrupt before completion

### Streaming Audio

#### Live Audio Input (16kHz PCM)

The API accepts continuous audio streams from the microphone:

```python
# Capture audio in chunks
audio_chunk = await audio_handler.get_input_audio()

# Send to Gemini
await session.send_realtime_input(
    audio={"data": audio_chunk["data"], "mime_type": "audio/pcm"}
)
```

**Format requirements:**
- Sample rate: 16,000 Hz
- Bit depth: 16-bit
- Channels: Mono (1 channel)
- Encoding: PCM (raw audio)

#### Live Audio Output (24kHz PCM)

The model responds with audio at a higher sample rate:

```python
async for response in session.receive():
    if response.data is not None:
        # response.data contains 24kHz PCM audio
        await audio_handler.queue_output_audio(response.data)
```

**Format:**
- Sample rate: 24,000 Hz
- Bit depth: 16-bit
- Channels: Mono
- Encoding: PCM

**Why different sample rates?**
- Input: 16kHz is sufficient for speech recognition (human voice range)
- Output: 24kHz provides better audio quality for synthesized speech

### Multimodal Turns Within a Single Session

A single session can handle multiple modalities simultaneously:

```python
# Turn 1: Audio input → Audio output
await session.send_audio(audio_data, "audio/pcm")

# Turn 2: Text input → Audio output
await session.send_text("What's the weather?")

# Turn 3: Audio + Tool call → Audio output
# (Model automatically invokes tools based on audio input)
```

**Supported combinations:**
- Audio in → Audio out
- Text in → Audio out
- Audio in → Text out (transcription)
- Audio in → Tool call → Audio out

### How the Model Determines Turn Boundaries

The Live API uses **Voice Activity Detection (VAD)** to determine when a user has finished speaking:

**Detection mechanisms:**
1. **Silence detection**: Pause longer than threshold (configurable)
2. **Prosody analysis**: Falling intonation patterns
3. **Semantic completeness**: Sentence/phrase completion

**Configuration:**
```python
config = {
    "automatic_activity_detection": {
        "start_sensitivity": "MEDIUM",  # How quickly to start responding
        "end_sensitivity": "MEDIUM",    # How long to wait for more speech
    }
}
```

**Sensitivity levels:**
- `LOW`: Wait longer (fewer false starts, more latency)
- `MEDIUM`: Balanced
- `HIGH`: Respond quickly (more responsive, may cut off)

---

## 3. Tool Use in Live Sessions

### How Tools Are Called Mid-Generation

Unlike standard APIs where tool calls happen between turns, Live API can invoke tools **during response generation**:

```
User: "What's the weather in Paris?"
  ↓
Model starts generating: "Let me check the weather for you..."
  ↓
Model pauses generation
  ↓
Model invokes: get_weather(location="Paris")
  ↓
Tool executes and returns: {"temp": 15, "conditions": "cloudy"}
  ↓
Model resumes generation: "...it's currently 15°C and cloudy in Paris."
```

### How Generation is Paused for Tool Execution

**Flow diagram:**
```
┌──────────────────┐
│ Model Generating │
└────────┬─────────┘
         │ Needs external data
         ▼
┌──────────────────┐
│ Pause Generation │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Send Tool Call   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Wait for Result  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Resume Generation │
└──────────────────┘
```

**Code example:**
```python
async for response in session.receive():
    # Check for tool calls
    if response.tool_call:
        # Generation is paused here
        print(f"🔧 Tool called: {response.tool_call.function_calls}")
        
        # Execute tools
        results = await tool_executor.execute_multiple(
            response.tool_call.function_calls
        )
        
        # Send results back
        await session.send_tool_response(function_responses=results)
        
        # Generation will resume automatically
```

### How Tool Results Are Injected Back

Tool results are sent as `FunctionResponse` objects:

```python
from google.genai import types

function_response = types.FunctionResponse(
    id=function_call.id,  # Must match the call ID
    name=function_call.name,
    response={
        "result": {
            "temperature": 15,
            "conditions": "cloudy"
        }
    }
)

await session.send_tool_response(function_responses=[function_response])
```

**Critical:** The `id` field must match the original function call ID, or the model won't be able to correlate the response.

### How Generation Resumes After Tool Output

Once tool results are sent, the model:
1. Incorporates the data into its context
2. Continues generating from where it paused
3. Seamlessly integrates the information into the response

**No additional action needed** — resumption is automatic.

### Example: Real-Time Google Search

```python
# Configure session with Google Search
config = {
    "tools": [{"google_search": {}}],
    "response_modalities": ["AUDIO"],
}

async with client.aio.live.connect(model=model, config=config) as session:
    await session.send_text("When did the last Olympics happen?")
    
    async for response in session.receive():
        # Model may execute Python code to search
        if response.server_content and response.server_content.model_turn:
            for part in response.server_content.model_turn.parts:
                if part.executable_code:
                    print(f"Search query: {part.executable_code.code}")
                if part.code_execution_result:
                    print(f"Search result: {part.code_execution_result.output}")
```

**Note:** Google Search is built-in and doesn't require function calling setup. The model automatically generates and executes search queries.

### Example: Real-Time Weather Lookup

```python
# Define weather function
weather_tool = {
    "function_declarations": [{
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }]
}

config = {"tools": [weather_tool]}

async with client.aio.live.connect(model=model, config=config) as session:
    await session.send_text("What's the weather in Tokyo?")
    
    async for response in session.receive():
        if response.tool_call:
            # Execute weather API call
            result = await get_weather(location="Tokyo")
            
            # Send back to model
            await session.send_tool_response(
                function_responses=[
                    types.FunctionResponse(
                        id=response.tool_call.function_calls[0].id,
                        name="get_weather",
                        response={"result": result}
                    )
                ]
            )
```

---

## 4. Session Management

### Maintaining Conversational State Across Turns

The Live API automatically maintains conversation history within a session:

```python
# Turn 1
await session.send_text("My name is Alice")
# Response: "Nice to meet you, Alice!"

# Turn 2 (model remembers context)
await session.send_text("What's my name?")
# Response: "Your name is Alice."
```

**How it works:**
- Each turn is appended to the session's context window
- Model has access to all previous turns
- Context is maintained until session ends or is reset

**Context window limits:**
- Native audio models: 128,000 tokens
- Other Live API models: 32,000 tokens

### Resetting vs Closing vs Reusing a Session

**Reset (Clear Context):**
```python
await session.reset()
# - Closes current connection
# - Clears conversation history
# - Opens new connection
# - Same session configuration
```

**Close (End Session):**
```python
await session.disconnect()
# - Closes connection
# - Releases resources
# - Cannot be reused
```

**Reuse (Continue Session):**
```python
# Just keep using the same session object
await session.send_text("Another question")
# - Maintains all context
# - No reconnection needed
```

### Handling Interruptions (User Speaks While Model is Responding)

**Barge-in support:**

```python
async for response in session.receive():
    # Check for interruption
    if response.server_content and response.server_content.interrupted:
        print("User interrupted!")
        
        # Clear audio output queue (stop playing old response)
        audio_handler.clear_output_queue()
        
        # Model will start generating new response
```

**What happens:**
1. User starts speaking while model is responding
2. Model detects interruption via VAD
3. Model stops current generation
4. `interrupted` flag is set in response
5. Model starts processing new user input

**Best practice:** Always clear audio output queue on interruption to avoid playing stale responses.

### Handling Partial Responses and Recovery

**Partial response scenario:**
```python
try:
    async for response in session.receive():
        if response.data:
            await audio_handler.queue_output_audio(response.data)
except ConnectionError:
    # Connection dropped mid-response
    print("Connection lost during response")
```

**Recovery strategies:**

1. **Session Resumption** (recommended):
```python
config = {
    "session_resumption": {},  # Enable resumption
}

# After disconnect, use resumption token to reconnect
# Context is preserved
```

2. **Retry with Context**:
```python
# Re-send the last user input
await session.send_text(last_user_message)
```

3. **Graceful Degradation**:
```python
# Inform user of partial response
print("Response was incomplete. Please try again.")
```

### Context Window Compression

For long conversations, enable automatic compression:

```python
config = {
    "context_window_compression": {
        "sliding_window": {
            "turn_coverage": 10  # Keep last 10 turns in full detail
        }
    }
}
```

**How it works:**
- Older turns are summarized/compressed
- Recent turns remain in full detail
- Prevents hitting token limits
- Enables unlimited conversation length

---

## 5. Ephemeral Tokens

### Why Ephemeral Tokens Are Required

**Security problem:**
```javascript
// NEVER DO THIS
const apiKey = "AIza...";  // Exposed in client-side code
const session = await gemini.connect({ apiKey });
```

**Why this is dangerous:**
- API keys visible in browser DevTools
- Keys can be extracted from JavaScript bundles
- Compromised keys can be used for unlimited API calls
- No way to revoke access for specific users

**Solution: Ephemeral Tokens**
```javascript
// Secure approach
const token = await fetch('/api/token').then(r => r.json());
const session = await gemini.connect({ token: token.value });
```

### Secure Server-Side Generation

**Backend (Python/FastAPI):**
```python
from google import genai
import datetime

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),  # Kept secret on server
    http_options={"api_version": "v1alpha"},
)

@app.post("/api/token")
async def generate_token():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    
    token = client.auth_tokens.create(
        config={
            "uses": 1,  # Single session
            "expire_time": now + datetime.timedelta(minutes=30),
            "new_session_expire_time": now + datetime.timedelta(minutes=1),
        }
    )
    
    return {"token": token.name}
```

**Security benefits:**
- API key never leaves server
- Tokens are short-lived
- Can restrict token capabilities
- Can track token usage per user

### Client-Side Usage Patterns

**Browser (JavaScript):**
```javascript
async function connectToGemini() {
    // 1. Fetch token from your backend
    const response = await fetch('https://your-backend.com/api/token', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${userAuthToken}`,  // Your app's auth
        },
    });
    
    const { token } = await response.json();
    
    // 2. Connect to Gemini with ephemeral token
    const session = await ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-12-2025',
        config: { responseModalities: ['AUDIO'] },
        // Use token instead of API key
        callbacks: {
            onopen: () => console.log('Connected'),
        },
    });
    
    // 3. Use session normally
    session.sendRealtimeInput({ audio: audioData });
}
```

### Token Expiry Behavior

**Two expiration times:**

1. **`new_session_expire_time`** (default: 1 minute)
   - How long you have to **start** a new session
   - After this, token cannot initiate new connections
   
2. **`expire_time`** (default: 30 minutes)
   - How long an **active** session can continue
   - After this, session is forcibly closed

**Timeline:**
```
Token created
    │
    ├─ 0:00 - Token issued
    │
    ├─ 0:30 - new_session_expire_time reached
    │          (can no longer start NEW sessions)
    │
    ├─ 1:00 - Active session still running
    │
    ├─ 29:00 - Active session still running
    │
    └─ 30:00 - expire_time reached
               (session forcibly closed)
```

### Token Renewal Strategy

**Proactive renewal:**
```javascript
class TokenManager {
    constructor() {
        this.token = null;
        this.expiresAt = null;
    }
    
    async getToken() {
        const now = new Date();
        
        // Renew if token expires in < 5 minutes
        if (!this.token || (this.expiresAt - now) < 5 * 60 * 1000) {
            await this.renewToken();
        }
        
        return this.token;
    }
    
    async renewToken() {
        const response = await fetch('/api/token', { method: 'POST' });
        const data = await response.json();
        
        this.token = data.token;
        this.expiresAt = new Date(data.expires_at);
    }
}
```

**Session resumption with same token:**
```python
# Server: Create token with session resumption
token = client.auth_tokens.create(
    config={
        "uses": 1,  # Can still resume with same token
        "expire_time": now + datetime.timedelta(minutes=30),
        "session_resumption": {},  # Enable resumption
    }
)
```

**Note:** Even with `uses: 1`, you can reconnect using session resumption within the `expire_time` window.

### Security Best Practices

1. **Never expose API keys:**
   ```python
   # ✅ Good: API key in environment variable
   api_key = os.getenv("GOOGLE_API_KEY")
   
   # ❌ Bad: API key in code
   api_key = "AIza..."
   ```

2. **Authenticate users before issuing tokens:**
   ```python
   @app.post("/api/token")
   async def generate_token(user: User = Depends(get_current_user)):
       # Only issue tokens to authenticated users
       if not user.is_authenticated:
           raise HTTPException(401, "Unauthorized")
   ```

3. **Set minimal token lifetimes:**
   ```python
   # Short-lived tokens
   expire_time = now + datetime.timedelta(minutes=30)
   
   # Long-lived tokens (security risk)
   expire_time = now + datetime.timedelta(days=30)
   ```

4. **Lock tokens to specific configurations:**
   ```python
   token = client.auth_tokens.create(
       config={
           "live_connect_constraints": {
               "model": "gemini-2.5-flash-native-audio-preview-12-2025",
               "config": {
                   "response_modalities": ["AUDIO"],
                   # Client cannot change these settings
               }
           }
       }
   )
   ```

5. **Rate limit token generation:**
   ```python
   from fastapi_limiter import FastAPILimiter
   
   @app.post("/api/token")
   @limiter.limit("10/minute")  # Max 10 tokens per minute per IP
   async def generate_token():
       ...
   ```

6. **Log token usage:**
   ```python
   @app.post("/api/token")
   async def generate_token(user: User):
       token = client.auth_tokens.create(...)
       
       # Log for audit trail
       logger.info(f"Token issued to user {user.id}")
       
       return {"token": token.name}
   ```

---

## Summary

The Gemini Live API enables real-time, low-latency AI interactions through:

1. **Persistent WebSocket connections** for bidirectional streaming
2. **Real-time audio I/O** with voice activity detection
3. **Mid-generation tool calling** for dynamic information retrieval
4. **Stateful session management** with context preservation
5. **Ephemeral tokens** for secure client-side access

Understanding these concepts is crucial for building production-ready live AI assistants that are responsive, secure, and reliable.
