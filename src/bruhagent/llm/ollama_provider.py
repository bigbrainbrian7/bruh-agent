from ollama import ResponseError, chat

from bruhagent.models import PlanExtraction

from .base import ProviderResponseError, ProviderUnavailableError


class OllamaProvider:
    """Generate plan extractions with a locally running Ollama model."""

    def __init__(self, model: str):
        self.model = model

    def analyze_plan(self, prompt: str) -> PlanExtraction:
        try:
            response = chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format=PlanExtraction.model_json_schema(),
                think=False,
                keep_alive="1m",
                options={
                    "temperature": 0, 
                },
            )
        except ResponseError as error:
            raise ProviderUnavailableError(str(error)) from error
        except ConnectionError as error:
            raise ProviderUnavailableError(
                "Cannot connect to Ollama at http://localhost:11434."
            ) from error

        try:
            return PlanExtraction.model_validate_json(response.message.content)
        except ValueError as error:
            raise ProviderResponseError("Ollama returned invalid plan data.") from error
