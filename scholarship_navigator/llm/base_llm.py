"""
llm/base_llm.py — Abstract Base Interface for all LLM providers.

All provider implementations (Ollama, OpenAI, etc.) must subclass BaseLLM
and implement the `generate` method. Agents interact ONLY through this
interface — they never import provider-specific clients directly.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLM(ABC):
    """
    Abstract base class for LLM provider adapters.

    Contract:
        - `generate(prompt)` must return the model's text response as a string.
        - Implementations must handle retries, timeouts, and errors internally.
        - Implementations must log all requests/responses via the LLM logger.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Send a prompt to the model and return the generated text.

        Args:
            prompt:          The input prompt string.
            response_format: Optional hint — "json" forces JSON-only output.

        Returns:
            The model's text response.

        Raises:
            LLMConnectionError:  If the provider endpoint is unreachable.
            LLMTimeoutError:     If the request exceeds the configured timeout.
            LLMResponseError:    If the response is malformed or empty.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# ---------------------------------------------------------------------------
# Custom exceptions — agents catch these instead of provider-specific errors
# ---------------------------------------------------------------------------

class LLMConnectionError(Exception):
    """Raised when the LLM provider endpoint cannot be reached."""


class LLMTimeoutError(Exception):
    """Raised when a request to the LLM provider exceeds the timeout."""


class LLMResponseError(Exception):
    """Raised when the LLM provider returns a malformed or empty response."""
