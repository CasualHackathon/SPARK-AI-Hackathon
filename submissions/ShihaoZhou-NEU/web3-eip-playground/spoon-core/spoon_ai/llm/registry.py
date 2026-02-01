"""
LLM Provider Registry for dynamic provider registration and discovery.
"""

from typing import Dict, Type, List, Optional, Any
from logging import getLogger

from .interface import LLMProviderInterface, ProviderCapability
from .errors import ConfigurationError, ProviderError

logger = getLogger(__name__)


class LLMProviderRegistry:
    """Registry for managing LLM provider classes and instances."""

    def __init__(self):
        self._providers: Dict[str, Type[LLMProviderInterface]] = {}
        self._instances: Dict[str, LLMProviderInterface] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, provider_class: Type[LLMProviderInterface]) -> None:
        """Register a provider class.

        Args:
            name: Unique provider name
            provider_class: Provider class implementing LLMProviderInterface

        Raises:
            ConfigurationError: If provider name already exists or class is invalid
        """
        if not issubclass(provider_class, LLMProviderInterface):
            raise ConfigurationError(
                f"Provider class must implement LLMProviderInterface",
                context={"provider_name": name, "class": provider_class.__name__}
            )

        if name in self._providers:
            logger.warning(f"Provider '{name}' already registered, overwriting")

        self._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    def get_provider(self, name: str, config: Optional[Dict[str, Any]] = None) -> LLMProviderInterface:
        """Get or create provider instance.

        Args:
            name: Provider name
            config: Provider configuration (optional if already configured)

        Returns:
            LLMProviderInterface: Provider instance

        Raises:
            ConfigurationError: If provider not found or configuration invalid
        """
        if name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ConfigurationError(
                f"Provider '{name}' not found. Available providers: {available}",
                context={"requested_provider": name, "available_providers": list(self._providers.keys())}
            )

        # Use provided config or stored config
        if config is not None:
            self._configs[name] = config
        elif name not in self._configs:
            raise ConfigurationError(
                f"No configuration provided for provider '{name}'",
                context={"provider_name": name}
            )

        # Return existing instance if available and config hasn't changed
        if name in self._instances:
            return self._instances[name]

        # Create new instance
        try:
            provider_class = self._providers[name]
            instance = provider_class()

            # Initialize with configuration
            import inspect
            if inspect.iscoroutinefunction(instance.initialize):
                # For async initialization, we'll need to handle this in the manager
                # For now, store the config and let the manager handle initialization
                pass

            self._instances[name] = instance
            logger.info(f"Created provider instance: {name}")
            return instance

        except Exception as e:
            raise ProviderError(
                name,
                f"Failed to create provider instance: {str(e)}",
                original_error=e,
                context={"provider_name": name, "config": self._configs.get(name)}
            )

    def list_providers(self) -> List[str]:
        """List all registered provider names.

        Returns:
            List[str]: List of provider names
        """
        return list(self._providers.keys())

    def get_capabilities(self, name: str) -> List[ProviderCapability]:
        """Get provider capabilities.

        Args:
            name: Provider name

        Returns:
            List[ProviderCapability]: List of supported capabilities

        Raises:
            ConfigurationError: If provider not found
        """
        if name not in self._providers:
            raise ConfigurationError(f"Provider '{name}' not found")

        # Try to get capabilities from existing instance first
        if name in self._instances:
            try:
                metadata = self._instances[name].get_metadata()
                return metadata.capabilities
            except Exception as e:
                logger.warning(f"Failed to get capabilities from instance for {name}: {e}")

        # If no instance available, try to get declared capabilities from the provider class
        try:
            provider_class = self._providers[name]
            if hasattr(provider_class, '_declared_capabilities'):
                logger.debug(f"Using declared capabilities for {name}: {provider_class._declared_capabilities}")
                return provider_class._declared_capabilities
        except Exception as e:
            logger.warning(f"Failed to get declared capabilities for {name}: {e}")

        # If no declared capabilities, return empty list
        logger.warning(f"No capabilities found for provider {name}, returning empty list")
        return []

    def is_registered(self, name: str) -> bool:
        """Check if a provider is registered.

        Args:
            name: Provider name

        Returns:
            bool: True if provider is registered
        """
        return name in self._providers

    def unregister(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: Provider name
        """
        if name in self._instances:
            # Cleanup instance if it exists
            try:
                import asyncio
                if asyncio.iscoroutinefunction(self._instances[name].cleanup):
                    # Note: This is synchronous cleanup, async cleanup should be handled by manager
                    pass
            except Exception as e:
                logger.warning(f"Error during cleanup of provider {name}: {e}")

            del self._instances[name]

        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered provider: {name}")

        if name in self._configs:
            del self._configs[name]

    def clear(self) -> None:
        """Clear all registered providers and instances."""
        # Cleanup all instances
        for name in list(self._instances.keys()):
            self.unregister(name)

        self._providers.clear()
        self._configs.clear()
        logger.info("Cleared all providers from registry")


# Global registry instance
_global_registry = LLMProviderRegistry()


def register_provider(name: str, capabilities: Optional[List[ProviderCapability]] = None):
    """Decorator for automatic provider registration.

    Args:
        name: Provider name
        capabilities: List of supported capabilities (optional)

    Returns:
        Decorator function
    """
    def decorator(cls: Type[LLMProviderInterface]):
        _global_registry.register(name, cls)

        # Store capabilities as class attribute if provided
        if capabilities:
            cls._declared_capabilities = capabilities

        return cls
    return decorator


def get_global_registry() -> LLMProviderRegistry:
    """Get the global provider registry instance.

    Returns:
        LLMProviderRegistry: Global registry instance
    """
    return _global_registry