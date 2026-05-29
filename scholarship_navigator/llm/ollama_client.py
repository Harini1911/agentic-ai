"""
llm/ollama_client.py — Ollama / Self-Hosted Gemma Client

Implements BaseLLM for the self-hosted Gemma model running behind an Ollama
server at OLLAMA_BASE_URL. Supports three API formats:

    API_TYPE = "ollama"            → POST /api/chat    (Ollama native)
    API_TYPE = "openai_compatible" → POST /chat/completions
    API_TYPE = "custom"            → POST /llm         (raw REST)

All retries, timeouts, and logging are handled here. Agents never see
provider-specific error types — only LLMConnectionError / LLMTimeoutError /
LLMResponseError from base_llm.py.
"""
import asyncio
import json
import time
from typing import Optional

import urllib.request
import urllib.error

from llm.base_llm import BaseLLM, LLMConnectionError, LLMTimeoutError, LLMResponseError
from config.llm_config import (
    OLLAMA_BASE_URL,
    LLM_MODEL,
    API_TYPE,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES,
    LLM_RETRY_DELAY,
)
from llm.llm_logger import llm_logger


class OllamaGemmaClient(BaseLLM):
    """
    Adapter for self-hosted Gemma via Ollama.

    Responsibilities:
        - Connect to OLLAMA_BASE_URL
        - Format requests according to API_TYPE
        - Send prompts and parse responses
        - Retry on transient failures with exponential backoff
        - Log every request/response with latency metrics
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = LLM_MODEL,
        api_type: str = API_TYPE,
        timeout: int = LLM_TIMEOUT,
        max_retries: int = LLM_MAX_RETRIES,
        retry_delay: float = LLM_RETRY_DELAY,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_type = api_type
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Send a prompt to the self-hosted Gemma model and return the response.

        Args:
            prompt:          The input text prompt.
            response_format: Pass "json" to request JSON-only output.

        Returns:
            Model's generated text as a plain string.

        Raises:
            LLMConnectionError:  Endpoint unreachable after all retries.
            LLMTimeoutError:     All retries timed out.
            LLMResponseError:    Response could not be parsed.
        """
        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(1, self.max_retries + 1):
            start_time = time.monotonic()
            try:
                llm_logger.info(
                    f"[LLM Request] Provider: Ollama | Model: {self.model} | "
                    f"API Type: {self.api_type} | Attempt: {attempt}/{self.max_retries} | "
                    f"Prompt length: {len(prompt)} chars"
                )

                # Run synchronous HTTP call in a thread to keep the event loop free
                raw_response = await asyncio.get_event_loop().run_in_executor(
                    None, self._sync_request, prompt, response_format
                )

                latency = time.monotonic() - start_time
                llm_logger.info(
                    f"[LLM Response] Provider: Ollama | Model: {self.model} | "
                    f"Latency: {latency:.2f}s | Response length: {len(raw_response)} chars"
                )

                return raw_response

            except LLMTimeoutError as e:
                latency = time.monotonic() - start_time
                llm_logger.warning(
                    f"[LLM Timeout] Attempt {attempt}/{self.max_retries} | "
                    f"Elapsed: {latency:.2f}s | Error: {e}"
                )
                last_error = e

            except LLMConnectionError as e:
                latency = time.monotonic() - start_time
                llm_logger.error(
                    f"[LLM Connection Error] Attempt {attempt}/{self.max_retries} | "
                    f"Elapsed: {latency:.2f}s | Error: {e}"
                )
                last_error = e

            except LLMResponseError as e:
                latency = time.monotonic() - start_time
                llm_logger.error(
                    f"[LLM Response Error] Attempt {attempt}/{self.max_retries} | "
                    f"Elapsed: {latency:.2f}s | Error: {e}"
                )
                last_error = e
                # Response errors are not transient — don't retry
                raise

            if attempt < self.max_retries:
                backoff = self.retry_delay * (2 ** (attempt - 1))
                llm_logger.info(f"[LLM Retry] Waiting {backoff:.1f}s before retry {attempt + 1}...")
                await asyncio.sleep(backoff)

        # All retries exhausted
        llm_logger.error(
            f"[LLM Failure] All {self.max_retries} retries exhausted. "
            f"Last error: {last_error}"
        )
        raise last_error

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sync_request(self, prompt: str, response_format: Optional[str]) -> str:
        """
        Synchronous HTTP request dispatcher.
        Routes to the appropriate format handler based on API_TYPE.
        """
        if self.api_type == "openai_compatible":
            return self._call_openai_compatible(prompt, response_format)
        elif self.api_type == "custom":
            return self._call_custom(prompt, response_format)
        else:
            # Default: ollama native
            return self._call_ollama_native(prompt, response_format)

    def _post_json(self, endpoint: str, payload: dict) -> dict:
        """
        Shared HTTP POST utility. Raises typed LLM exceptions.
        If endpoint is empty, POSTs directly to base_url.
        """
        url = self.base_url if not endpoint else f"{self.base_url}{endpoint}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as e:
                    llm_logger.error(f"[LLM Raw Response] {raw[:500]}")
                    raise LLMResponseError(
                        f"Could not parse JSON from provider response: {e}"
                    ) from e
        except urllib.error.URLError as e:
            reason = str(e.reason) if hasattr(e, "reason") else str(e)
            if "timed out" in reason.lower():
                raise LLMTimeoutError(
                    f"Request to {url} timed out after {self.timeout}s"
                ) from e
            raise LLMConnectionError(
                f"Unable to reach {url}: {reason}"
            ) from e
        except TimeoutError as e:
            raise LLMTimeoutError(
                f"Request to {url} timed out after {self.timeout}s"
            ) from e

    def _call_ollama_native(self, prompt: str, response_format: Optional[str]) -> str:
        """Ollama native format: POST /api/chat"""
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        if response_format == "json":
            payload["format"] = "json"

        data = self._post_json("/api/chat", payload)
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as e:
            raise LLMResponseError(
                f"Unexpected Ollama response structure: {data}"
            ) from e

    def _call_openai_compatible(self, prompt: str, response_format: Optional[str]) -> str:
        """
        OpenAI-compatible format.

        Tries two URL patterns:
          1. POST directly to base_url (handles endpoints like http://host/llm)
          2. POST to base_url/chat/completions (standard OpenAI path)
        """
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        # Try direct POST to base_url first
        try:
            data = self._post_json("", payload)
            return data["choices"][0]["message"]["content"]
        except (LLMResponseError, LLMConnectionError, KeyError, IndexError, TypeError):
            pass

        # Fallback: standard /chat/completions path
        data = self._post_json("/chat/completions", payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMResponseError(
                f"Unexpected OpenAI-compatible response structure: {data}"
            ) from e


    def _call_custom(self, prompt: str, response_format: Optional[str]) -> str:
        """Custom REST format: POST /llm"""
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
        }
        if response_format == "json":
            payload["response_format"] = "json"

        data = self._post_json("/llm", payload)
        # Try common response key patterns
        for key in ("response", "output", "text", "content", "generated_text"):
            if key in data:
                return str(data[key])
        # Fall back to full response as string
        return str(data)

    def __repr__(self) -> str:
        return (
            f"OllamaGemmaClient("
            f"model={self.model!r}, "
            f"api_type={self.api_type!r}, "
            f"base_url={self.base_url!r})"
        )
