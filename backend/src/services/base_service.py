"""
Base service class for all external service wrappers.

All services in src/services/ inherit from this base class to ensure
consistent initialization, health checks, logging, and error handling.

Usage:
    class MyService(BaseService[MyServiceConfig]):
        def _initialize(self) -> None:
            # Set up connections/clients
            pass

        def health_check(self) -> bool:
            # Verify service is reachable
            return True
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import structlog

# Generic type for service-specific configuration
ConfigT = TypeVar("ConfigT")


class BaseService(ABC, Generic[ConfigT]):
    """
    Abstract base class for all external service wrappers.

    Provides:
    - Consistent initialization pattern
    - Health check interface
    - Logging setup
    - Configuration access

    All external service access MUST go through service classes that
    inherit from this base. No direct connector/client instantiation
    elsewhere in the codebase.
    """

    def __init__(self, config: ConfigT):
        """
        Initialize the service with configuration.

        Args:
            config: Service-specific configuration dataclass.
        """
        self._config = config
        self._log = structlog.get_logger().bind(service=self.__class__.__name__)
        self._initialized = False

        # Call subclass initialization
        self._initialize()
        self._initialized = True

        self._log.info("service_initialized")

    @abstractmethod
    def _initialize(self) -> None:
        """
        Set up connections, clients, or pools.

        Called once during construction. Subclasses must implement this
        to establish their specific connections.

        Raises:
            Exception: If initialization fails (fail fast at startup).
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify service is reachable and credentials are valid.

        Called at application startup to validate all services before
        accepting requests. Should be quick and non-destructive.

        Returns:
            True if service is healthy.

        Raises:
            Exception: With details if health check fails.
        """
        pass

    @property
    def config(self) -> ConfigT:
        """Access the service configuration."""
        return self._config

    @property
    def log(self) -> structlog.stdlib.BoundLogger:
        """Access the service logger."""
        return self._log

    @property
    def is_initialized(self) -> bool:
        """Check if service has been initialized."""
        return self._initialized

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} initialized={self._initialized}>"
