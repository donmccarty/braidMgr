"""
API routes for braidMgr backend.

Exports:
    health: Health check and root endpoints
    auth: Authentication endpoints
"""

from src.api.routes import health
from src.api.routes import auth

__all__ = ["health", "auth"]
