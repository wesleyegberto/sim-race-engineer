"""Tests for setup_advisor.llm_client — all LLM calls are mocked."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from simraceengineer.analysis.setup_advisor.llm_client import (
    AnthropicClient,
    LLMClientBase,
    OllamaClient,
    create_client,
)
from simraceengineer.config import AppConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides: object) -> AppConfig:
    """Return an AppConfig with LLM fields overridden."""
    cfg = AppConfig()
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


# ---------------------------------------------------------------------------
# create_client factory
# ---------------------------------------------------------------------------

class TestCreateClient:
    def test_ollama_backend_returns_ollama_client(self) -> None:
        cfg = _make_config(llm_backend="ollama", llm_base_url="http://localhost:11434", llm_model="gemma4:12b")
        client = create_client(cfg)
        assert isinstance(client, OllamaClient)

    def test_anthropic_backend_returns_anthropic_client(self) -> None:
        cfg = _make_config(llm_backend="anthropic", llm_api_key="sk-test", llm_model="claude-3-5-sonnet-20241022")
        client = create_client(cfg)
        assert isinstance(client, AnthropicClient)

    def test_ollama_backend_case_insensitive(self) -> None:
        cfg = _make_config(llm_backend="Ollama")
        client = create_client(cfg)
        assert isinstance(client, OllamaClient)

    def test_anthropic_backend_case_insensitive(self) -> None:
        cfg = _make_config(llm_backend="Anthropic", llm_api_key="sk-x")
        client = create_client(cfg)
        assert isinstance(client, AnthropicClient)

    def test_invalid_backend_raises_value_error(self) -> None:
        cfg = _make_config(llm_backend="unknown-backend")
        with pytest.raises(ValueError, match="Backend LLM desconhecido"):
            create_client(cfg)

    def test_invalid_backend_message_contains_valid_options(self) -> None:
        cfg = _make_config(llm_backend="gpt4")
        with pytest.raises(ValueError, match="ollama.*anthropic"):
            create_client(cfg)

    def test_client_is_subclass_of_base(self) -> None:
        cfg = _make_config(llm_backend="ollama")
        client = create_client(cfg)
        assert isinstance(client, LLMClientBase)


# ---------------------------------------------------------------------------
# OllamaClient.generate
# ---------------------------------------------------------------------------

class TestOllamaClientGenerate:
    def test_generate_returns_string(self) -> None:
        mock_ollama = MagicMock()
        mock_client_instance = MagicMock()
        mock_ollama.Client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = {
            "message": {"content": "Use stiffer front ARB."}
        }

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            client = OllamaClient(base_url="http://localhost:11434", model="gemma4:12b")
            result = client.generate("What setup change for understeer?")

        assert result == "Use stiffer front ARB."

    def test_generate_passes_prompt_as_user_message(self) -> None:
        mock_ollama = MagicMock()
        mock_client_instance = MagicMock()
        mock_ollama.Client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = {"message": {"content": "OK"}}

        prompt = "Adjust camber?"
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            client = OllamaClient(base_url="http://x", model="my-model")
            client.generate(prompt)

        call_kwargs = mock_client_instance.chat.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[1]
        assert any(m["role"] == "user" and m["content"] == prompt for m in messages)

    def test_generate_uses_configured_model(self) -> None:
        mock_ollama = MagicMock()
        mock_client_instance = MagicMock()
        mock_ollama.Client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = {"message": {"content": "OK"}}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            client = OllamaClient(base_url="http://x", model="llama3")
            client.generate("hello")

        call_kwargs = mock_client_instance.chat.call_args
        model_arg = call_kwargs.kwargs.get("model") or call_kwargs.args[0]
        assert model_arg == "llama3"

    def test_generate_with_system_prepends_system_message(self) -> None:
        mock_ollama = MagicMock()
        mock_client_instance = MagicMock()
        mock_ollama.Client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = {"message": {"content": "OK"}}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            client = OllamaClient(base_url="http://x", model="m")
            client.generate("user prompt", system="you are an engineer")

        messages = mock_client_instance.chat.call_args.kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "you are an engineer"}
        assert messages[1] == {"role": "user", "content": "user prompt"}

    def test_generate_without_system_sends_only_user_message(self) -> None:
        mock_ollama = MagicMock()
        mock_client_instance = MagicMock()
        mock_ollama.Client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = {"message": {"content": "OK"}}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            client = OllamaClient(base_url="http://x", model="m")
            client.generate("user only")

        messages = mock_client_instance.chat.call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_generate_raises_import_error_when_sdk_missing(self) -> None:
        with patch.dict(sys.modules, {"ollama": None}):  # type: ignore[dict-item]
            client = OllamaClient(base_url="http://x", model="m")
            with pytest.raises(ImportError, match="uv pip install"):
                client.generate("test")


# ---------------------------------------------------------------------------
# AnthropicClient.generate
# ---------------------------------------------------------------------------

class TestAnthropicClientGenerate:
    def _make_mock_anthropic(self, response_text: str) -> MagicMock:
        mock_anthropic = MagicMock()
        mock_api = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_api

        content_block = MagicMock()
        content_block.text = response_text
        mock_message = MagicMock()
        mock_message.content = [content_block]
        mock_api.messages.create.return_value = mock_message

        return mock_anthropic

    def test_generate_returns_string(self) -> None:
        mock_anthropic = self._make_mock_anthropic("Lower ride height.")

        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            client = AnthropicClient(api_key="sk-test", model="claude-3-5-sonnet-20241022")
            result = client.generate("Setup advice?")

        assert result == "Lower ride height."

    def test_generate_passes_api_key(self) -> None:
        mock_anthropic = self._make_mock_anthropic("OK")

        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            client = AnthropicClient(api_key="sk-secret", model="claude-3-5-sonnet-20241022")
            client.generate("test")

        mock_anthropic.Anthropic.assert_called_once_with(api_key="sk-secret")

    def test_generate_passes_prompt_as_user_message(self) -> None:
        mock_anthropic = self._make_mock_anthropic("OK")
        prompt = "Brake bias?"

        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            client = AnthropicClient(api_key="k", model="claude-3-5-sonnet-20241022")
            client.generate(prompt)

        mock_api = mock_anthropic.Anthropic.return_value
        call_kwargs = mock_api.messages.create.call_args
        messages = call_kwargs.kwargs.get("messages", [])
        assert any(m["role"] == "user" and m["content"] == prompt for m in messages)

    def test_generate_uses_configured_model(self) -> None:
        mock_anthropic = self._make_mock_anthropic("OK")

        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            client = AnthropicClient(api_key="k", model="claude-opus-4-5")
            client.generate("x")

        mock_api = mock_anthropic.Anthropic.return_value
        call_kwargs = mock_api.messages.create.call_args
        model_arg = call_kwargs.kwargs.get("model")
        assert model_arg == "claude-opus-4-5"

    def test_generate_with_system_passes_system_kwarg(self) -> None:
        mock_anthropic = self._make_mock_anthropic("OK")

        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            client = AnthropicClient(api_key="k", model="claude-3-5-sonnet-20241022")
            client.generate("user msg", system="you are an engineer")

        mock_api = mock_anthropic.Anthropic.return_value
        call_kwargs = mock_api.messages.create.call_args.kwargs
        assert call_kwargs.get("system") == "you are an engineer"

    def test_generate_without_system_omits_system_kwarg(self) -> None:
        mock_anthropic = self._make_mock_anthropic("OK")

        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            client = AnthropicClient(api_key="k", model="claude-3-5-sonnet-20241022")
            client.generate("user msg")

        mock_api = mock_anthropic.Anthropic.return_value
        call_kwargs = mock_api.messages.create.call_args.kwargs
        assert "system" not in call_kwargs

    def test_generate_raises_import_error_when_sdk_missing(self) -> None:
        with patch.dict(sys.modules, {"anthropic": None}):  # type: ignore[dict-item]
            client = AnthropicClient(api_key="k", model="m")
            with pytest.raises(ImportError, match="uv pip install"):
                client.generate("test")
