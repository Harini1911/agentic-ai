# Day 01 - Google ADK Quickstart

**Date:** January 7, 2026  
**Topic:** Python Quickstart for Google Agent Development Kit (ADK)  
**Status:** Completed

---

## Overview

Today marked the first step into building AI agents with Google's Agent Development Kit (ADK). Successfully created, configured, and ran a research agent in both CLI and web-based modes.

---

## Concepts Learned

### What is Google ADK?

The **Google Agent Development Kit (ADK)** is a Python framework for building intelligent, autonomous agents powered by Google's Gemini models. Unlike simple chatbots, ADK agents can:

- **Think and reason** using Gemini's advanced language models
- **Use tools** to access external data and perform actions
- **Maintain context** across conversations
- **Be deployed** via CLI, web interface, or cloud services

### Key ADK Components

#### 1. **Agent** (`google.adk.agents.llm_agent.Agent`)
The core building block that defines:
- **Model:** Which Gemini model to use (e.g., `gemini-2.5-flash`)
- **Name:** Identifier for the agent
- **Description:** What the agent does
- **Instruction:** System-level instructions on how the agent should behave
- **Tools:** Functions the agent can call (optional)

#### 2. **Environment Configuration**
ADK uses **environment variables** to securely store credentials:
- `GOOGLE_API_KEY`: Your Gemini API key from Google AI Studio
- Stored in `.env` files (gitignored for security)

#### 3. **Project Structure**
ADK follows a modular structure:
```
adk_research_agent/
├── .adk/                    # ADK-specific metadata and storage
├── .env                     # Environment variables (API keys)
├── __init__.py             # Makes directory a Python package
└── agent.py                # Agent definition (entry point)
```

> **Why this structure?**  
> - `.adk/` stores session data and local configurations
> - `.env` keeps secrets separate from code (security best practice)
> - `agent.py` exports `root_agent` that ADK CLI automatically discovers

---

## How It Fits Into the Project

### Before Today
```
agentic-ai/
├── examples/           # Gemini API experiments
├── t2t-bot/           # Custom text-to-text bot
├── live-api/          # Live API experiments
└── research-agent/    # Earlier research attempts
```

### After Today
```
agentic-ai/
├── adk_research_agent/        # NEW: Production-ready ADK agent
│    ├── docs/                      # NEW: Documentation folder
│    │   └── day-01-adk-quickstart.md
│    ├── .adk/                 # Session storage
│    ├── .env                  # API key configuration
│    ├── __init__.py
│    └── agent.py              # Agent definition
├── examples/
├── t2t-bot/
├── live-api/
└── research-agent/
```

### Integration Points

1. **Shares Dependencies:** Uses the same `uv` virtual environment and `pyproject.toml`
2. **Follows Conventions:** Adopts the repository's `.env` pattern
3. **Complements Existing Work:** ADK agents are higher-level than raw API calls in `examples/`

---

## Tasks Completed

### 1. Created Agent Project
```bash
# Created new ADK agent directory
adk_research_agent/
```

**What happened:**
- ADK expects each agent in its own folder
- Folder name becomes the agent identifier for the CLI

---

### 2. Explored Agent Structure

Examined the minimal agent configuration:

```python
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)
```

**Why these parameters?**
- `model`: Specifies which Gemini model to use (flash = faster, cheaper)
- `name`: Used in logs and session tracking
- `description`: Helps when composing multiple agents
- `instruction`: Acts as the "system prompt" guiding agent behavior

---

### 3. Updated Agent with Code

Added a mock tool function:

```python
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}
```

**Purpose:**
- Demonstrates tool structure (tools are just Python functions)
- Shows how agents can be extended with custom capabilities
- Currently unused but ready to be registered with the agent

---

### 4. Set API Key

Created `.env` file with proper encoding:

```bash
GOOGLE_API_KEY=your_api_key_here
```

#### Challenges Encountered & Solved

**Problem 1: UnicodeDecodeError**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```
- **Cause:** Corrupted `.env` file with invalid encoding
- **Solution:** Deleted and recreated file with proper UTF-8 encoding

**Problem 2: Missing API Key Error**
```
ValueError: Missing key inputs argument! To use the Google AI API, provide ('api_key') arguments.
```
- **Cause:** `.env` file had UTF-8 BOM (Byte Order Mark) preventing dotenv parser from reading
- **Solution:** Recreated file using UTF-8 **without BOM**:
  ```powershell
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText("path\.env", "GOOGLE_API_KEY=key", $utf8NoBom)
  ```

> **Key Learning:** PowerShell's `Set-Content -Encoding UTF8` adds BOM by default, which breaks python-dotenv!

---

### 5. Ran Agent

#### CLI Mode
```bash
cd c:\Users\Harini - ITEL\Desktop\agentic-ai
uv run adk run adk_research_agent
```

**Output:**
```
Running agent root_agent, type exit to exit.
[user]: Hello, what can you help me with?
[root_agent]: I can help with a variety of things! Here are a few examples:
1. Answer questions on various topics...
[user]: exit
```

**Why this works:**
- `uv run` activates virtual environment and runs ADK CLI
- `adk run adk_research_agent` loads the agent folder
- ADK finds `agent.py` and imports `root_agent`
- Interactive REPL starts for real-time conversation

#### Web-Based Mode
```bash
uv run adk web --port 8000
```

**Output:**
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

**Features:**
- Web UI at `http://127.0.0.1:8000/dev-ui/`
- Select agent from dropdown
- Interactive chat interface with session management
- Better for demos and development

---

## Code Quality & Best Practices

### 1. **Clean & Modular**
- Separation of concerns: Agent definition in `agent.py`  
- Environment variables in `.env` (not hardcoded)  
- Minimal dependencies (only what's needed)

### 2. **Security**
- API keys in `.env` (gitignored)  
- Never commit secrets to version control  
- `.gitignore` includes `.env` pattern

### 3. **ADK Best Practices**

#### DO:
- Export agent as `root_agent` variable in `agent.py`
- Use `.env` files for configuration
- Keep agents in separate directories
- Use descriptive names and instructions
- Let ADK auto-configure from environment

#### DON'T:
- Manually create `Client` instances (ADK handles this)
- Pass `client` parameter to `Agent()` (causes Pydantic validation error)
- Use UTF-8 with BOM for `.env` files
- Hardcode API keys in Python files

### 4. **Comments & Documentation**

The code includes:
- **Docstrings** for functions (explains what tools do)
- **Comments** explaining "why" (e.g., "Mock tool implementation")
- **Type hints** for clarity (`city: str -> dict`)

---

## Debugging Tips

### Inspect `.env` Encoding
```powershell
Format-Hex .\adk_research_agent\.env | Select-Object -First 3
```
- Should start with `47 4F 4F...` (GOOGLE_API_KEY)
- Should NOT start with `EF BB BF` (UTF-8 BOM)

### Check Environment Loading
```bash
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv('.env'); print(os.getenv('GOOGLE_API_KEY'))"
```

### View ADK Logs
```bash
# Logs are written to temp directory
tail -F C:\Users\HARINI~1\AppData\Local\Temp\agents_log\agent.*.log
```

---

## What Should Be Documented?

For each day's learning, document:

### 1. **Concept Overview**
- What new concept/feature was learned?
- Why is it important?
- How does it work at a high level?

### 2. **Project Integration**
- Where does it fit in the existing structure?
- What files were created/modified?
- How does it connect to previous work?

### 3. **Implementation Details**
- Code snippets with explanations
- Key decisions and trade-offs
- Best practices followed

### 4. **Challenges & Solutions**
- Problems encountered
- Root cause analysis
- Solutions implemented

### 5. **Running Instructions**
- Exact commands to reproduce
- Expected output
- Common errors and fixes

### 6. **Next Steps**
- What to explore next
- Open questions
- Improvement ideas

---

## Git Commit Message

```
feat(adk): add Day 1 ADK quickstart agent and documentation

- Create adk_research_agent with Gemini 2.5 Flash
- Configure environment variables with proper UTF-8 encoding
- Add mock tool implementation (get_current_time)
- Test agent in both CLI and web modes
- Document ADK concepts, project structure, and best practices
- Troubleshoot and fix .env encoding issues (UTF-8 BOM removal)
- Add comprehensive Day 1 documentation in docs/day-01-adk-quickstart.md

Closes #N/A
```

**Alternative (shorter):**
```
feat: Day 1 - Google ADK quickstart with research agent

- Features:
- Working ADK agent with Gemini 2.5 Flash
- CLI interface: uv run adk run adk_research_agent
- Web interface: uv run adk web --port 8000
- Comprehensive troubleshooting documentation
- Best practices and code quality guidelines
```

## Resources

- [Google ADK Documentation](https://cloud.google.com/vertex-ai/docs/adk)
- [Gemini API](https://ai.google.dev/)
- [Python dotenv](https://github.com/theskumar/python-dotenv)

---

**End of Day 1 - Great progress!**
