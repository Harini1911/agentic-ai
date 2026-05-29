"""
config/llm_config.py — Centralized LLM Configuration

Single source of truth for all model and provider settings.
Agents must NEVER hardcode model names or provider URLs.
To swap models, change only this file (or the corresponding .env variables).
"""
import os
from dotenv import load_dotenv

# Load .env from the scholarship_navigator directory
load_dotenv()

# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

# ---------------------------------------------------------------------------
# Ollama / Self-Hosted Gemma endpoint
# OLLAMA_BASE_URL must be set in .env — never hardcode the server address here.
# ---------------------------------------------------------------------------
_ollama_base_url = os.getenv("OLLAMA_BASE_URL")
if not _ollama_base_url:
    raise RuntimeError(
        "OLLAMA_BASE_URL not set in environment.\n"
        "Add it to scholarship_navigator/.env:\n"
        "  OLLAMA_BASE_URL=http://<your-server>/llm\n"
        "Never hardcode server addresses in source files."
    )
OLLAMA_BASE_URL: str = _ollama_base_url
LLM_MODEL: str = os.getenv("LLM_MODEL", "google/gemma-4-26B-A4B-it")

# ---------------------------------------------------------------------------
# API type — controls which request format the OllamaGemmaClient uses
#   ollama            → POST /api/chat   (Ollama native)
#   openai_compatible → POST /chat/completions (OpenAI-compatible)
#   custom            → POST /llm        (raw REST)
# ---------------------------------------------------------------------------
API_TYPE: str = os.getenv("API_TYPE", "openai_compatible")

# ---------------------------------------------------------------------------
# Retry / timeout settings
# ---------------------------------------------------------------------------
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "120"))
LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_RETRY_DELAY: float = float(os.getenv("LLM_RETRY_DELAY", "2.0"))

# ---------------------------------------------------------------------------
# ADK model string — used in Agent(model=...) declarations.
#
# ADK uses litellm under the hood. For custom (non-localhost) endpoints the
# "openai/" provider prefix + OPENAI_API_BASE env var is the most reliable
# litellm pattern. ADK_MODEL is always read from .env — never hardcoded here.
#
# Default falls back to openai/<model> if ADK_MODEL is not in .env.
# ---------------------------------------------------------------------------
ADK_MODEL: str = os.getenv("ADK_MODEL", f"openai/{LLM_MODEL}")

# ---------------------------------------------------------------------------
# Propagate litellm routing env vars from .env into os.environ so that
# litellm picks them up even when loaded as a module (not from a shell).
# The actual URL values come from .env — not from this file.
# ---------------------------------------------------------------------------
_openai_api_base = os.getenv("OPENAI_API_BASE")
if _openai_api_base:
    os.environ["OPENAI_API_BASE"] = _openai_api_base

_openai_api_key = os.getenv("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_API_KEY", _openai_api_key)

_ollama_api_base = os.getenv("OLLAMA_API_BASE")
if _ollama_api_base:
    os.environ["OLLAMA_API_BASE"] = _ollama_api_base
