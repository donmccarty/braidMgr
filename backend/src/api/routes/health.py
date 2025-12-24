"""
Health check endpoints for braidMgr API.

Provides:
- /health: Basic health check with service status
- /: Root endpoint with API info

Usage:
    # Include in main.py
    from src.api.routes import health
    app.include_router(health.router)
"""

from fastapi import APIRouter

from src.services import services


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns status of all services for load balancer health probes.

    Returns:
        Dictionary with overall status and per-service health.
    """
    return {
        "status": "healthy",
        "services": services.health_check_all(),
    }


@router.get("/")
async def root() -> dict:
    """
    Root endpoint with API info.

    Returns:
        Dictionary with API name, version, and docs link.
    """
    return {
        "name": "braidMgr API",
        "version": "0.1.0",
        "docs": "/docs",
    }
