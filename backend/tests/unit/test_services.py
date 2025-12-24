"""
Unit tests for src/services/

Tests the service registry and base service:
- ServiceRegistry singleton behavior
- BaseService abstract class
- AuroraService configuration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from src.services import services, ServiceRegistry
from src.services.base_service import BaseService
from src.services.aurora_service import AuroraService, AuroraConfig
from src.config.settings import AppConfig


class TestServiceRegistry:
    """Tests for ServiceRegistry singleton."""

    def setup_method(self):
        """Reset registry before each test."""
        # Access internal state to reset
        ServiceRegistry._instance = None
        ServiceRegistry._initialized = False

    def test_singleton_pattern(self):
        """ServiceRegistry is a singleton."""
        reg1 = ServiceRegistry()
        reg2 = ServiceRegistry()
        assert reg1 is reg2

    def test_not_initialized_by_default(self):
        """Registry is not initialized by default."""
        registry = ServiceRegistry()
        assert registry.is_initialized is False

    def test_accessing_service_before_init_raises(self):
        """Accessing services before initialize() raises RuntimeError."""
        registry = ServiceRegistry()
        with pytest.raises(RuntimeError) as exc_info:
            _ = registry.aurora
        assert "not initialized" in str(exc_info.value).lower()

    def test_initialize_sets_flag(self):
        """initialize() sets is_initialized to True."""
        registry = ServiceRegistry()

        # Create mock config with nested mock structure
        mock_pool = Mock()
        mock_pool.min_connections = 1
        mock_pool.max_connections = 5
        mock_pool.connection_timeout = 10

        mock_database = Mock()
        mock_database.host = "localhost"
        mock_database.port = 5432
        mock_database.name = "test_db"
        mock_database.user = "test_user"
        mock_database.password = "test_pass"
        mock_database.pool = mock_pool

        mock_config = Mock()
        mock_config.database = mock_database

        registry.initialize(mock_config)
        assert registry.is_initialized is True

    def test_double_initialize_is_noop(self):
        """Calling initialize() twice doesn't re-initialize."""
        registry = ServiceRegistry()

        # Create mock config with nested mock structure
        mock_pool = Mock()
        mock_pool.min_connections = 1
        mock_pool.max_connections = 5
        mock_pool.connection_timeout = 10

        mock_database = Mock()
        mock_database.host = "localhost"
        mock_database.port = 5432
        mock_database.name = "test_db"
        mock_database.user = "test_user"
        mock_database.password = "test_pass"
        mock_database.pool = mock_pool

        mock_config = Mock()
        mock_config.database = mock_database

        registry.initialize(mock_config)
        aurora1 = registry.aurora

        registry.initialize(mock_config)  # Second call
        aurora2 = registry.aurora

        # Same service instance
        assert aurora1 is aurora2

    def test_aurora_service_accessible_after_init(self):
        """Aurora service is accessible after initialize()."""
        registry = ServiceRegistry()

        # Create mock config with nested mock structure
        mock_pool = Mock()
        mock_pool.min_connections = 1
        mock_pool.max_connections = 5
        mock_pool.connection_timeout = 10

        mock_database = Mock()
        mock_database.host = "localhost"
        mock_database.port = 5432
        mock_database.name = "test_db"
        mock_database.user = "test_user"
        mock_database.password = "test_pass"
        mock_database.pool = mock_pool

        mock_config = Mock()
        mock_config.database = mock_database

        registry.initialize(mock_config)

        aurora = registry.aurora
        assert isinstance(aurora, AuroraService)

    def test_global_services_instance(self):
        """Global 'services' is a ServiceRegistry instance."""
        from src.services import services
        assert isinstance(services, ServiceRegistry)


class TestBaseService:
    """Tests for BaseService abstract class."""

    def test_base_service_is_abstract(self):
        """Cannot instantiate BaseService directly."""
        # BaseService has abstract methods, can't be instantiated directly
        with pytest.raises(TypeError):
            BaseService({})

    def test_concrete_service_requires_initialize(self):
        """Concrete service must implement _initialize()."""

        # Missing _initialize implementation
        with pytest.raises(TypeError):
            @dataclass
            class IncompleteConfig:
                pass

            class IncompleteService(BaseService):
                def health_check(self) -> bool:
                    return True

            IncompleteService(IncompleteConfig())

    def test_concrete_service_requires_health_check(self):
        """Concrete service must implement health_check()."""

        with pytest.raises(TypeError):
            @dataclass
            class IncompleteConfig:
                pass

            class IncompleteService(BaseService):
                def _initialize(self) -> None:
                    pass

            IncompleteService(IncompleteConfig())

    def test_concrete_service_initialization(self):
        """Properly implemented concrete service initializes correctly."""

        @dataclass
        class TestConfig:
            value: str = "test"

        class TestService(BaseService[TestConfig]):
            def _initialize(self) -> None:
                self.initialized_value = self._config.value

            def health_check(self) -> bool:
                return True

        config = TestConfig(value="hello")
        service = TestService(config)

        assert service.is_initialized is True
        assert service.initialized_value == "hello"
        assert service.config.value == "hello"

    def test_service_has_logger(self):
        """Service has a bound logger with service name."""

        @dataclass
        class TestConfig:
            pass

        class TestService(BaseService[TestConfig]):
            def _initialize(self) -> None:
                pass

            def health_check(self) -> bool:
                return True

        service = TestService(TestConfig())
        assert service.log is not None

    def test_service_repr(self):
        """Service has a useful repr."""

        @dataclass
        class TestConfig:
            pass

        class MyTestService(BaseService[TestConfig]):
            def _initialize(self) -> None:
                pass

            def health_check(self) -> bool:
                return True

        service = MyTestService(TestConfig())
        repr_str = repr(service)
        assert "MyTestService" in repr_str
        assert "initialized=True" in repr_str


class TestAuroraConfig:
    """Tests for AuroraConfig dataclass."""

    def test_default_values(self):
        """AuroraConfig has sensible defaults."""
        config = AuroraConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "braidmgr_dev"
        assert config.user == "postgres"
        assert config.password == "postgres"
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.connection_timeout == 30

    def test_custom_values(self):
        """AuroraConfig accepts custom values."""
        config = AuroraConfig(
            host="db.example.com",
            port=5433,
            name="production_db",
            user="prod_user",
            password="prod_pass",
            min_connections=5,
            max_connections=20,
            connection_timeout=60,
        )
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.name == "production_db"
        assert config.min_connections == 5


class TestAuroraService:
    """Tests for AuroraService (unit tests without actual DB connection)."""

    def test_initialization(self):
        """AuroraService initializes without connecting."""
        config = AuroraConfig(
            host="localhost",
            port=5432,
            name="test_db",
        )
        service = AuroraService(config)
        assert service.is_initialized is True
        # Pool is not created yet (lazy initialization)
        assert service._pool is None

    def test_dsn_construction(self):
        """DSN is correctly constructed from config."""
        config = AuroraConfig(
            host="myhost",
            port=5433,
            name="mydb",
            user="myuser",
            password="mypass",
        )
        service = AuroraService(config)

        # DSN should contain all components
        assert "myhost" in service._dsn
        assert "5433" in service._dsn
        assert "mydb" in service._dsn
        assert "myuser" in service._dsn
        assert "mypass" in service._dsn

    def test_config_accessible(self):
        """Config is accessible via property."""
        config = AuroraConfig(host="testhost")
        service = AuroraService(config)
        assert service.config.host == "testhost"


class TestAuroraServiceAsync:
    """Async tests for AuroraService (mocked)."""

    @pytest.fixture
    def aurora_service(self):
        """Create AuroraService for testing."""
        config = AuroraConfig(
            host="localhost",
            port=5432,
            name="test_db",
        )
        return AuroraService(config)

    @pytest.mark.asyncio
    async def test_close_without_pool(self, aurora_service):
        """close() is safe to call without pool."""
        # Should not raise even with no pool
        await aurora_service.close()
        assert aurora_service._pool is None

    @pytest.mark.asyncio
    async def test_close_with_mock_pool(self, aurora_service):
        """close() closes the pool."""
        mock_pool = AsyncMock()
        aurora_service._pool = mock_pool

        await aurora_service.close()

        mock_pool.close.assert_called_once()
        assert aurora_service._pool is None
