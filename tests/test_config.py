import os
import unittest
from unittest.mock import patch

from src.agents.base import create_chat_model
from src.utils.config import LLMSettings, MCPSettings, OllamaSettings, OpenAISettings, get_config
from src.utils.mcp_manager import MCPServerManager


class ProviderConfigTests(unittest.TestCase):
    def tearDown(self):
        get_config.cache_clear()

    def test_ollama_provider_does_not_require_openai_key(self):
        settings = LLMSettings(
            provider="ollama",
            ollama=OllamaSettings(model="qwen2.5:7b"),
        )
        model, provider = create_chat_model(settings)

        self.assertEqual(provider, "ollama")
        self.assertEqual(model.model, "qwen2.5:7b")

    def test_openai_provider_uses_configured_key_environment_variable(self):
        settings = LLMSettings(
            provider="openai",
            openai=OpenAISettings(
                model="gpt-4.1-mini",
                api_key_env="TEST_MARKETSCOUT_OPENAI_KEY",
            ),
        )
        with patch.dict(os.environ, {"TEST_MARKETSCOUT_OPENAI_KEY": "test-key"}, clear=False):
            model, provider = create_chat_model(settings)

        self.assertEqual(provider, "openai")
        self.assertEqual(model.model_name, "gpt-4.1-mini")

    def test_mcp_settings_validate_positive_timeouts(self):
        settings = MCPSettings(url="http://tools.example/sse", tool_timeout_seconds=5)
        self.assertEqual(settings.url, "http://tools.example/sse")
        self.assertEqual(settings.tool_timeout_seconds, 5)

    def test_mcp_manager_uses_configured_server_url(self):
        with patch("src.utils.mcp_manager.get_config") as get_config:
            get_config.return_value.mcp = MCPSettings(url="http://tools.example:8123/sse")
            manager = MCPServerManager()

        self.assertEqual(manager.base_url, "http://tools.example:8123")


if __name__ == "__main__":
    unittest.main()
