from abc import ABC
from typing import Dict, Generic, TypeVar

T = TypeVar("T", bound=ABC)


class GenericProviderFactory(Generic[T]):
    """Generic factory for creating provider instances."""

    def __init__(self, provider_type_name: str):
        """
        Initialize the factory.

        Args:
            provider_type_name: Human-readable name for error messages
        """
        self._providers: Dict[str, type[T]] = {}
        self._provider_type_name = provider_type_name

    def register(self, name: str, provider_class: type[T]) -> None:
        """Register a provider."""
        self._providers[name.lower()] = provider_class

    def create(self, provider_name: str, **kwargs) -> T:
        """Create a provider instance."""
        provider_class = self._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown {self._provider_type_name} provider: {provider_name}")
        return provider_class(**kwargs)

    def available_providers(self) -> list[str]:
        """Return list of available providers."""
        return list(self._providers.keys())
