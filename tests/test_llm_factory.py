import os
import unittest
from unittest.mock import patch

from bruhagent.llm import ProviderAuthenticationError, create_provider
from bruhagent.llm.gemini_provider import GeminiProvider
from bruhagent.llm.ollama_provider import OllamaProvider


class ProviderFactoryTests(unittest.TestCase):
    def test_ollama_uses_the_default_model(self) -> None:
        provider = create_provider("ollama")

        self.assertIsInstance(provider, OllamaProvider)
        self.assertEqual(provider.model, "qwen3:1.7b")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False)
    def test_creates_gemini_provider(self) -> None:
        provider = create_provider("gemini", "test-model")

        self.assertIsInstance(provider, GeminiProvider)
