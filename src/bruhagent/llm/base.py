from typing import Protocol

from bruhagent.models import PlanExtraction


class LLMError(Exception):
    """Base error for language-model providers."""


class ProviderAuthenticationError(LLMError):
    """The configured API key is missing or was rejected."""


class ProviderUnavailableError(LLMError):
    """The configured provider cannot be reached."""


class ProviderResponseError(LLMError):
    """The provider response could not be used as a plan extraction."""


class LLMProvider(Protocol):
    def analyze_plan(self, prompt: str) -> PlanExtraction:
        """Analyze a plan and extract relevant information."""
        ...
