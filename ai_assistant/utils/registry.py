from typing import Dict, Type, TypeVar, Optional
from core.interfaces import audio, speech, assistant, clipboard

T = TypeVar("T")


class ProviderRegistry:
    _instance = None

    def __init__(self):
        self._providers: Dict[Type, object] = {}
        self._configs: Dict[Type, dict] = {}

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_provider(
        self, interface_type: Type[T], provider: T, config: Optional[dict] = None
    ) -> None:
        """Register a provider implementation for an interface"""
        self._providers[interface_type] = provider
        if config:
            self._configs[interface_type] = config

    def get_provider(self, interface_type: Type[T]) -> Optional[T]:
        """Get the registered provider for an interface"""
        return self._providers.get(interface_type)

    def get_config(self, interface_type: Type[T]) -> Optional[dict]:
        """Get the configuration for a provider"""
        return self._configs.get(interface_type)

    def clear(self) -> None:
        """Clear all registered providers"""
        self._providers.clear()
        self._configs.clear()
