from logging import config
import os

from google import genai
from google.genai._gaos.lib import compat_errors

from bruhagent.models import PlanExtraction

from .base import (
    ProviderAuthenticationError,
    ProviderResponseError,
    ProviderUnavailableError,
)


class GeminiProvider:
    """Generate plan extractions with the Gemini Interactions API."""

    def __init__(self, model: str):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ProviderAuthenticationError(
                "Set GEMINI_API_KEY before using the Gemini provider."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def analyze_plan(self, prompt: str) -> PlanExtraction:
        try:
            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt,
                store=False,
                response_format=[
                    {
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": PlanExtraction.model_json_schema(),
                    }
                ],
                generation_config={
                    "thinking_level": "minimal",  # Minimizes thinking for faster response times
                    # TODO: still randomizes
                    "temperature": 0,  # Disables randomization for consistent responses
                }
            )
        except (
            compat_errors.AuthenticationError,
            compat_errors.PermissionDeniedError,
        ) as error:
            raise ProviderAuthenticationError("Gemini rejected GEMINI_API_KEY.") from error
        except (
            compat_errors.APIConnectionError,
            compat_errors.APITimeoutError,
            compat_errors.InternalServerError,
            compat_errors.RateLimitError,
        ) as error:
            raise ProviderUnavailableError("Gemini is temporarily unavailable.") from error
        except compat_errors.APIError as error:
            raise ProviderResponseError(f"Gemini API error: {error}") from error
        except OSError as error:
            raise ProviderUnavailableError("Cannot connect to the Gemini API.") from error

        if not interaction.output_text:
            raise ProviderResponseError("Gemini returned an empty response.")

        try:
            return PlanExtraction.model_validate_json(interaction.output_text)
        except ValueError as error:
            raise ProviderResponseError("Gemini returned invalid plan data.") from error
