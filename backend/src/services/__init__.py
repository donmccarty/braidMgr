"""
Service Registry - Centralized access to all external services.

All external service access MUST go through this registry.
No direct connector/client instantiation elsewhere in the codebase.

Usage:
    from src.services import services

    # Initialize at application startup
    from src.config import get_config
    services.initialize(get_config())

    # Access any service
    items = await services.aurora.execute_query("SELECT * FROM items")

    # Health check all services
    services.health_check_all()
"""

from typing import Optional

from src.config.settings import AppConfig
from src.services.base_service import BaseService
from src.services.aurora_service import AuroraService, AuroraConfig


class ServiceRegistry:
    """
    Centralized access point for all external services.

    Singleton pattern ensures services are initialized once at startup
    and shared across the application.

    Services available:
    - aurora: PostgreSQL/Aurora database access

    Future services:
    - anthropic: Claude AI for chat integration
    - s3: Document/attachment storage
    - email: Transactional emails
    """

    _instance: Optional["ServiceRegistry"] = None
    _initialized: bool = False

    def __new__(cls) -> "ServiceRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: AppConfig) -> None:
        """
        Initialize all services with configuration.

        Called once at application startup. Validates all connections
        before proceeding (fail fast).

        Args:
            config: Application configuration from config.yaml.

        Raises:
            RuntimeError: If already initialized (call reset() first).
            Exception: If any service fails to initialize.
        """
        if self._initialized:
            return

        # Build Aurora config from app config
        aurora_config = AuroraConfig(
            host=config.database.host,
            port=config.database.port,
            name=config.database.name,
            user=config.database.user,
            password=config.database.password,
            min_connections=config.database.pool.min_connections,
            max_connections=config.database.pool.max_connections,
            connection_timeout=config.database.pool.connection_timeout,
        )
        self._aurora = AuroraService(aurora_config)

        # Future services will be initialized here:
        # self._anthropic = AnthropicService(config.integrations.anthropic)
        # self._s3 = S3Service(config.aws.s3)

        self._initialized = True

    @property
    def aurora(self) -> AuroraService:
        """Access the Aurora/PostgreSQL service."""
        self._ensure_initialized()
        return self._aurora

    def health_check_all(self) -> dict:
        """
        Run health checks on all initialized services.

        Returns:
            Dict mapping service name to health status (True/False/error message).
        """
        self._ensure_initialized()
        results = {}

        # Check Aurora
        try:
            results["aurora"] = self._aurora.health_check()
        except Exception as e:
            results["aurora"] = str(e)

        # Future services will be checked here

        return results

    async def close_all(self) -> None:
        """
        Close all service connections (async).

        Call during application shutdown for graceful cleanup.
        """
        if hasattr(self, "_aurora"):
            await self._aurora.close()

        # Future services will be closed here

    def reset(self) -> None:
        """
        Reset the registry for testing or reconfiguration.

        Closes all connections and allows re-initialization.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.close_all())
        except RuntimeError:
            asyncio.run(self.close_all())
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Raise if services haven't been initialized."""
        if not self._initialized:
            raise RuntimeError(
                "ServiceRegistry not initialized. "
                "Call services.initialize(config) at application startup."
            )

    @property
    def is_initialized(self) -> bool:
        """Check if services have been initialized."""
        return self._initialized


# Singleton instance for import
services = ServiceRegistry()

# Export commonly used items
__all__ = [
    "services",
    "ServiceRegistry",
    "BaseService",
    "AuroraService",
    "AuroraConfig",
]
