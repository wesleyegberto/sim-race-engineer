"""LLM client abstraction supporting Ollama, Anthropic, and OpenAI-compatible backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from simracing.config import AppConfig


class LLMClientBase(ABC):
    """Abstract base for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send prompt and return generated text."""
        ...


class OllamaClient(LLMClientBase):
    """LLM client backed by a local Ollama instance."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            import ollama  # type: ignore[import]
        except ImportError:
            raise ImportError(
                "Instale o pacote ollama: uv pip install -e '.[advisor]'"
            )

        client = ollama.Client(host=self.base_url)
        response = client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]


class AnthropicClient(LLMClientBase):
    """LLM client backed by Anthropic API."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            import anthropic  # type: ignore[import]
        except ImportError:
            raise ImportError(
                "Instale o pacote anthropic: uv pip install -e '.[advisor]'"
            )

        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


class OpenAICompatClient(LLMClientBase):
    """LLM client for OpenAI-compatible APIs (LM Studio, LocalAI, vLLM, etc.).

    Configure llm_base_url to the server endpoint, e.g.:
      - LM Studio: http://localhost:1234/v1
      - LocalAI:   http://localhost:8080/v1
    Set llm_api_key to any non-empty string when the server does not require auth.
    """

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url
        self.api_key = api_key or "local"
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            from openai import OpenAI  # type: ignore[import]
        except ImportError:
            raise ImportError(
                "Instale o pacote openai: uv pip install -e '.[advisor]'"
            )

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return response.choices[0].message.content


def create_client(config: AppConfig) -> LLMClientBase:
    """Instantiate the correct LLM client from AppConfig.

    Args:
        config: Application configuration carrying llm_backend, llm_model,
                llm_api_key, and llm_base_url.

    Returns:
        Concrete LLMClientBase for the configured backend.

    Raises:
        ValueError: When llm_backend is not "ollama", "anthropic", or "openai".
    """
    backend = config.llm_backend.lower()

    if backend == "ollama":
        return OllamaClient(base_url=config.llm_base_url, model=config.llm_model)

    if backend == "anthropic":
        return AnthropicClient(api_key=config.llm_api_key, model=config.llm_model)

    if backend == "openai":
        return OpenAICompatClient(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            model=config.llm_model,
        )

    raise ValueError(
        f"Backend LLM desconhecido: '{config.llm_backend}'. "
        "Valores válidos: 'ollama', 'anthropic', 'openai'."
    )
