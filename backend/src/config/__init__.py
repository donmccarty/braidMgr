"""
Configuration management for braidMgr backend.

Exports:
    get_config: Get the singleton AppConfig instance
    AppConfig: Complete application configuration dataclass
"""

from src.config.settings import get_config, AppConfig

__all__ = ["get_config", "AppConfig"]
