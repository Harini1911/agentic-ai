"""
llm/llm_factory.py — LLM Provider Factory

The single entry point for all agent code that needs an LLM instance.
Agents call:

    from llm.llm_factory import get_llm
    llm = get_llm()
    response = await llm.generate(prompt)

To add a new provider:
    1. Create a new class in llm/ that subclasses BaseLLM.
    2. Add its import and a case in _build_llm() below.
    3. Set LLM_PROVIDER=<name> in .env.

No agent code needs to change when the provider changes.
"""
from typing import Optional
from llm.base_llm import BaseLLM
from config.llm_config import LLM_PROVIDER
from llm.llm_logger import llm_logger

# Module-level singleton — created once on first call to get_llm()
_llm_instance: Optional[BaseLLM] = None


def _build_llm() -> BaseLLM:
    """
    Instantiates the correct LLM client based on LLM_PROVIDER.
    """
    provider = LLM_PROVIDER.lower().strip()

    if provider == "ollama":
        from llm.ollama_client import OllamaGemmaClient
        from config.llm_config import OLLAMA_BASE_URL, LLM_MODEL, API_TYPE
        client = OllamaGemmaClient(
            base_url=OLLAMA_BASE_URL,
            model=LLM_MODEL,
            api_type=API_TYPE,
        )
        llm_logger.info(
            f"[LLM Factory] Initialized provider=ollama | "
            f"model={LLM_MODEL} | endpoint={OLLAMA_BASE_URL} | api_type={API_TYPE}"
        )
        return client

    # Future providers plug in here:
    # elif provider == "openai":
    #     from llm.openai_client import OpenAIClient
    #     return OpenAIClient()

    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. "
        f"Supported providers: ['ollama']. "
        f"Update config/llm_config.py and llm/llm_factory.py to add new providers."
    )


def get_llm() -> BaseLLM:
    """
    Returns the shared LLM instance (singleton).
    Creates it on first call, then reuses for all subsequent calls.
    Thread-safe for typical single-process async usage.
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _build_llm()
    return _llm_instance


def reset_llm() -> None:
    """
    Clears the cached instance. Useful for tests that need to swap providers.
    """
    global _llm_instance
    _llm_instance = None
