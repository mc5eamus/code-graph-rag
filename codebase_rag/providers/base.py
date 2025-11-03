"""Base provider interface and registry for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, cast
from urllib.parse import urljoin

import httpx
from loguru import logger

from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.models.openai import OpenAIChatModel

class ModelProvider(ABC):
    """Abstract base class for all model providers."""

    def __init__(self, **config: Any) -> None:
        """Initialize provider with configuration."""
        self.config = config

    @abstractmethod
    def create_model(self, model_id: str, **kwargs: Any) -> Any:
        """Create a model instance for this provider."""
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """Validate provider configuration and raise ValueError if invalid."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
class AzureOpenAIProvider(ModelProvider):
    """OpenAI provider."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.api_key = api_key
        self.endpoint = endpoint

    @property
    def provider_name(self) -> str:
        return "azureopenai"

    def validate_config(self) -> None:
        if not self.api_key:
            raise ValueError(
                "OpenAI provider requires api_key. "
                "Set ORCHESTRATOR_API_KEY or CYPHER_API_KEY in .env file."
            )

    def create_model(self, model_id: str, **kwargs: Any) -> OpenAIChatModel:
        self.validate_config()

        model = OpenAIChatModel(
            'gpt-5-mini',
            provider=AzureProvider(
            azure_endpoint=self.endpoint,
            api_version='2024-12-01-preview',
            api_key=self.api_key,
            )
        )

        return model 

# Provider registry
PROVIDER_REGISTRY: dict[str, type[ModelProvider]] = {
    "azureopenai": AzureOpenAIProvider,}


def get_provider(provider_name: str, **config: Any) -> ModelProvider:
    """Factory function to create a provider instance."""
    if provider_name not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available providers: {available}"
        )

    provider_class = PROVIDER_REGISTRY[provider_name]
    return provider_class(**config)


def register_provider(name: str, provider_class: type[ModelProvider]) -> None:
    """Register a new provider class."""
    PROVIDER_REGISTRY[name] = provider_class
    logger.info(f"Registered provider: {name}")


def list_providers() -> list[str]:
    """List all available provider names."""
    return list(PROVIDER_REGISTRY.keys())
