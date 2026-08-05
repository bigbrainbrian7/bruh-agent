from .base import LLMProvider


def create_provider(provider_name: str, model: str | None = None) -> LLMProvider:
    """Create the configured provider without leaking provider details upward."""
    match provider_name:
        case "ollama":
            from .ollama_provider import OllamaProvider

            return OllamaProvider(model=model or "qwen3:1.7b")
        case "gemini":
            from .gemini_provider import GeminiProvider

            return GeminiProvider(model=model or "gemini-3.5-flash-lite")
