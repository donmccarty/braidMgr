"""
Alembic migration environment for braidMgr.

Configures database connection from config.yaml for migrations.
"""

from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend/src to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.config import get_config

# Alembic Config object provides access to alembic.ini
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate (None for now - manual migrations)
target_metadata = None


def get_database_url() -> str:
    """
    Build database URL from config.yaml.

    Returns:
        SQLAlchemy-compatible connection string.
    """
    app_config = get_config()
    db = app_config.database
    return f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL script without connecting to database.
    Used for: alembic upgrade head --sql
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Connects to database and applies migrations directly.
    """
    # Override URL from config.yaml
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
