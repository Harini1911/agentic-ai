# Phase 9 — Self-Hosted LLM Integration (Gemma via Ollama)

## Objective

Refactor the Scholarship Navigator ADK project so that all agents use a **self-hosted Gemma model** instead of the managed Gemini Flash API.

The primary learning goal is:

**LLM Provider Decoupling — Agent Architecture ≠ Model Provider**

The ADK workflow architecture remains completely unchanged. Only the model backend is replaced.

---

## Architecture

```text
ADK Agents

      ↓

LLM Adapter Layer

      ↓

Self-Hosted Gemma

      ↓

<OLLAMA_BASE_URL>   ← set in .env only
```

---

## Why Replace Gemini?

| Factor | Gemini Flash (Managed) | Gemma (Self-Hosted) |
|--------|------------------------|---------------------|
| Cost | Per-token billing | Infrastructure cost only |
| Data Privacy | Sent to Google | Stays on your server |
| Rate Limits | Subject to quota | No external limits |
| Vendor Lock-in | Google Cloud | Portable to any server |
| Customization | Fixed model | Fine-tunable |
| API Keys | Required | Not needed |

---

## Key Insight

> **The ADK workflows did not change at all.**
>
> Router Workflow → unchanged  
> Sequential Workflow → unchanged  
> Parallel Workflow → unchanged  
> Loop Workflow → unchanged  
> Coordinator → unchanged  
> Memory Store → unchanged  
>
> Only the `model=` string in each `Agent()` declaration was replaced — from  
> `"gemini-2.5-flash"` → `ADK_MODEL` (read from `.env`).

---

## New Files Created

```text
scholarship_navigator/
├── config/
│   ├── __init__.py
│   └── llm_config.py          ← Centralized LLM configuration
│
├── llm/
│   ├── __init__.py
│   ├── base_llm.py            ← Abstract interface (BaseLLM)
│   ├── ollama_client.py       ← OllamaGemmaClient implementation
│   ├── llm_factory.py         ← Factory singleton (get_llm())
│   └── llm_logger.py          ← Structured request/response logger
│
└── logs/
    └── llm.log                ← Auto-created at runtime
```

---

## Configuration

All settings live in `.env` (never hardcoded in source):

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://<your-server>/llm
LLM_MODEL=google/gemma-4-26B-A4B-it
API_TYPE=ollama

ADK_MODEL=ollama/google/gemma-4-26B-A4B-it

LLM_TIMEOUT=120
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=2.0
```

---

## LLM Abstraction Layer

### BaseLLM Interface

```python
class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str, response_format=None) -> str:
        ...
```

All providers implement this single method. Agents never know which provider is running.

### OllamaGemmaClient

Supports three API formats auto-detected via `API_TYPE`:

| `API_TYPE` | Endpoint | Format |
|------------|----------|--------|
| `ollama` | `POST /api/chat` | Ollama native |
| `openai_compatible` | `POST /chat/completions` | OpenAI-compatible |
| `custom` | `POST /llm` | Raw REST |

### LLM Factory

```python
from llm.llm_factory import get_llm

llm = get_llm()                            # Singleton
response = await llm.generate(prompt)      # Provider-agnostic
```

---

## Agent Refactoring Pattern

### Before (Phase 8)
```python
# Hardcoded model + direct Gemini API calls
agent = Agent(name="...", model="gemini-2.5-flash", ...)

response = genai.Client(api_key=key).models.generate_content(...)
```

### After (Phase 9)
```python
# Model from config — provider-agnostic calls
from config.llm_config import ADK_MODEL
from llm.llm_factory import get_llm

agent = Agent(name="...", model=ADK_MODEL, ...)

llm = get_llm()
response = await llm.generate(prompt)
```

---

## Logging

Every LLM request and response is logged to `logs/llm.log`:

```
2026-05-29T10:25:01 [INFO] [LLM Request] Provider: Ollama | Model: google/gemma-4-26B-A4B-it | API Type: ollama | Attempt: 1/3 | Prompt length: 892 chars
2026-05-29T10:25:03 [INFO] [LLM Response] Provider: Ollama | Model: google/gemma-4-26B-A4B-it | Latency: 2.14s | Response length: 312 chars
```

---

## Error Handling

| Error | Class | Behavior |
|-------|-------|----------|
| Endpoint unreachable | `LLMConnectionError` | Retry with exponential backoff |
| Request timed out | `LLMTimeoutError` | Retry up to `LLM_MAX_RETRIES` |
| Malformed response | `LLMResponseError` | Log raw response, raise immediately |

---

## Future Provider Swap

To switch to a different provider (e.g. OpenAI), only two files change:

1. **`.env`**: `LLM_PROVIDER=openai`
2. **`llm/llm_factory.py`**: Add `elif provider == "openai": return OpenAIClient()`

No agent files change. No workflow files change. No business logic changes.

---

## ADK Concept Demonstrated

> **Agent Architecture ≠ Model Provider**
>
> The ADK Coordinator, Router, Sequential, Parallel, and Loop patterns are  
> **model-agnostic**. They define *how* agents are orchestrated, not *which*  
> model powers them.
>
> This phase demonstrates that the entire 8-phase system can be migrated to  
> a completely different LLM backend by changing only the configuration layer.
