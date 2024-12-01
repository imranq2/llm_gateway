from typing import (
    Any,
    Callable,
    Dict,
    Protocol,
    TypeVar,
    TypeAlias,
    runtime_checkable,
    cast,
)

T = TypeVar("T")
S = TypeVar("S")

# Type definitions
ServiceFactory: TypeAlias = Callable[["SimpleContainer"], T]


@runtime_checkable
class Injectable(Protocol):
    """Marker protocol for injectable services"""


class ContainerError(Exception):
    """Base exception for container errors"""


class ServiceNotFoundError(ContainerError):
    """Raised when a service is not found"""


class SimpleContainer:
    """Generic IoC Container"""

    def __init__(self) -> None:
        self._services: Dict[type[Any], Any] = {}
        self._factories: Dict[type[Any], ServiceFactory[Any]] = {}

    def register(
        self, service_type: type[T], factory: ServiceFactory[T]
    ) -> "SimpleContainer":
        """
        Register a service factory

        Args:
            service_type: The type of service to register
            factory: Factory function that creates the service
        """
        if not callable(factory):
            raise ValueError(f"Factory for {service_type} must be callable")

        self._factories[service_type] = factory
        return self

    def resolve(self, service_type: type[T]) -> T:
        """
        Resolve a service instance

        Args:
            service_type: The type of service to resolve

        Returns:
            An instance of the requested service
        """
        if service_type not in self._services:
            if service_type not in self._factories:
                raise ServiceNotFoundError(f"No factory registered for {service_type}")

            factory = self._factories[service_type]
            self._services[service_type] = factory(self)

        return cast(T, self._services[service_type])

    def singleton(self, service_type: type[T], instance: T) -> "SimpleContainer":
        """Register a singleton instance"""
        self._services[service_type] = instance
        return self

    def transient(
        self, service_type: type[T], factory: ServiceFactory[T]
    ) -> "SimpleContainer":
        """Register a transient service"""

        def create_new(container: SimpleContainer) -> T:
            return factory(container)

        self.register(service_type, create_new)
        return self
