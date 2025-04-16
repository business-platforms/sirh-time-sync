# src/core/dependency_container.py
import logging
from typing import Dict, Any, Type, Optional, TypeVar, Generic, cast

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """A simple dependency injection container."""

    def __init__(self):
        self._service: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}

    def register(self, name: str, instance: Any) -> None:
        """Register a service instance."""
        self._service[name] = instance
        logger.debug(f"Registered service: {name}")

    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function that creates a service instance."""
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")

    def get(self, name: str) -> Any:
        """Get a service by name."""
        # Return existing instance if available
        if name in self._service:
            return self._service[name]

        # Create instance from factory if available
        if name in self._factories:
            instance = self._factories[name](self)
            self._service[name] = instance
            return instance

        logger.error(f"Service not found: {name}")
        raise KeyError(f"Service not found: {name}")

    def get_typed(self, name: str, expected_type: Type[T]) -> T:
        """Get a service by name with type checking."""
        service = self.get(name)
        if not isinstance(service, expected_type):
            raise TypeError(f"Service {name} is not of type {expected_type.__name__}")
        return cast(expected_type, service)

    def remove(self, name: str) -> None:
        """Remove a service by name."""
        if name in self._service:
            del self._service[name]
        if name in self._factories:
            del self._factories[name]

    def clear(self) -> None:
        """Clear all registered service."""
        self._service.clear()
        self._factories.clear()