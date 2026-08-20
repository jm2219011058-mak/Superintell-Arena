"""
Unified LLM Client - LiteLLM adapter layer

Provides a single interface for calling multiple LLM providers
(OpenAI, Anthropic/Claude, DeepSeek, or any OpenAI-compatible endpoint)
through LiteLLM's unified API.

Usage:
    from app.services.llm_client import UnifiedLLMClient

    client = UnifiedLLMClient()
    response = client.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
    )
    print(response.choices[0].message.content)

    # For code that still needs the raw OpenAI client:
    openai_client = client.openai_compatible_client
"""

import logging
import time
from typing import Any, Dict, List, Optional

import litellm
from openai import OpenAI

from ..config import Config

logger = logging.getLogger("mirofish.unified_llm")

# Suppress litellm's verbose default logging
litellm.suppress_debug_info = True

# Provider -> litellm model prefix mapping
_PROVIDER_PREFIXES: Dict[str, str] = {
    "openai": "openai/",
    "anthropic": "anthropic/",
    "deepseek": "deepseek/",
    "azure": "azure/",
    "bedrock": "bedrock/",
    "vertex_ai": "vertex_ai/",
    "cohere": "cohere/",
    "mistral": "mistral/",
}

# Providers that do NOT need a base_url (they have native litellm support)
_NATIVE_PROVIDERS = {"anthropic", "deepseek", "azure", "bedrock", "vertex_ai", "cohere", "mistral"}


def _build_model_name(provider: str, model: str) -> str:
    """
    Build the litellm-compatible model identifier.

    If the model name already contains a '/' prefix matching the provider,
    return it as-is.  Otherwise prepend the provider prefix so litellm
    routes the request to the correct backend.

    For 'openai' with a custom base_url (OpenAI-compatible servers like
    vLLM, LocalAI, etc.) we use 'openai/' prefix so litellm sends the
    request to the configured base_url.
    """
    prefix = _PROVIDER_PREFIXES.get(provider, "")
    if prefix and model.startswith(prefix):
        return model
    # If model already has some other prefix (e.g. user set "anthropic/claude-3...")
    if "/" in model:
        return model
    return f"{prefix}{model}" if prefix else model


class UnifiedLLMClient:
    """
    Unified LLM client wrapping litellm.completion().

    Reads configuration from the Config class by default but accepts
    explicit overrides for provider, api_key, base_url, and model_name.

    Features:
      - Automatic provider-based model name mapping for litellm
      - Retry with exponential backoff (3 attempts)
      - Token usage logging for cost tracking
      - Backward-compatible OpenAI client property
    """

    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.provider = (provider or Config.LLM_PROVIDER or "openai").lower().strip()
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")

        # Build the litellm model identifier
        self._litellm_model = _build_model_name(self.provider, self.model_name)

        # For native providers, base_url is handled by litellm itself;
        # only pass it for openai-compatible or custom endpoints.
        self._use_custom_base_url = self.provider not in _NATIVE_PROVIDERS

        logger.info(
            "UnifiedLLMClient initialized: provider=%s, model=%s, litellm_model=%s, base_url=%s",
            self.provider,
            self.model_name,
            self._litellm_model,
            self.base_url if self._use_custom_base_url else "(native)",
        )

    # ------------------------------------------------------------------
    # Core completion method
    # ------------------------------------------------------------------

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Send a chat completion request through litellm.

        Args:
            messages: List of message dicts (role/content).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response. None lets the
                        provider use its default.
            response_format: E.g. {"type": "json_object"} for JSON mode.
            **kwargs: Additional parameters forwarded to litellm.completion().

        Returns:
            A litellm ModelResponse (same shape as OpenAI ChatCompletion).

        Raises:
            The last exception after all retries are exhausted.
        """
        call_kwargs: Dict[str, Any] = {
            "model": self._litellm_model,
            "messages": messages,
            "temperature": temperature,
            "api_key": self.api_key,
        }

        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens

        if response_format is not None:
            call_kwargs["response_format"] = response_format

        # Only pass base_url for openai-compatible / custom endpoints
        if self._use_custom_base_url and self.base_url:
            call_kwargs["api_base"] = self.base_url

        call_kwargs.update(kwargs)

        last_error: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = litellm.completion(**call_kwargs)
                self._log_usage(response, attempt)
                return response

            except Exception as exc:
                last_error = exc
                if attempt < self.MAX_RETRIES:
                    delay = self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "LLM call failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt,
                        self.MAX_RETRIES,
                        str(exc)[:120],
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "LLM call failed after %d attempts: %s",
                        self.MAX_RETRIES,
                        str(exc)[:200],
                    )

        raise last_error  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Return just the text content from a chat completion."""
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Send a request with JSON mode and parse the response."""
        import json
        import re

        text = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            **kwargs,
        )

        # Strip markdown code fences if present
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {cleaned[:200]}") from exc

    # ------------------------------------------------------------------
    # Backward-compatible OpenAI client
    # ------------------------------------------------------------------

    @property
    def openai_compatible_client(self) -> OpenAI:
        """
        Return an OpenAI SDK client for code that still needs the raw
        OpenAI interface (e.g. response_format, streaming, function calling).

        For native OpenAI or any OpenAI-compatible endpoint this works
        directly.  For Anthropic/DeepSeek with native keys, callers
        should prefer chat_completion() instead.
        """
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_usage(self, response: Any, attempt: int) -> None:
        """Log token usage from the response for cost tracking."""
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            total_tokens = getattr(usage, "total_tokens", 0) or 0
            logger.info(
                "LLM usage [%s, attempt %d]: prompt=%d, completion=%d, total=%d",
                self._litellm_model,
                attempt,
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )

    # ------------------------------------------------------------------
    # Class-level factory for boost config
    # ------------------------------------------------------------------

    @classmethod
    def create_boost_client(cls) -> Optional["UnifiedLLMClient"]:
        """
        Create a client using the boost LLM configuration, if available.

        Returns None if boost config is not set.
        """
        if not Config.LLM_BOOST_API_KEY:
            return None

        return cls(
            provider=Config.LLM_BOOST_PROVIDER or Config.LLM_PROVIDER or "openai",
            api_key=Config.LLM_BOOST_API_KEY,
            base_url=Config.LLM_BOOST_BASE_URL or Config.LLM_BASE_URL,
            model_name=Config.LLM_BOOST_MODEL_NAME or Config.LLM_MODEL_NAME,
        )


# Module-level convenience: a default client instance (lazy singleton)
_default_client: Optional[UnifiedLLMClient] = None


def get_default_client() -> UnifiedLLMClient:
    """Return (and lazily create) the default UnifiedLLMClient."""
    global _default_client
    if _default_client is None:
        _default_client = UnifiedLLMClient()
    return _default_client
