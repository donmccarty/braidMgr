"""
FastAPI application entry point for braidMgr.

Usage:
    # Development
    uvicorn src.api.main:app --reload --port 8000

    # Production
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_config
from src.services import services
from src.api.routes import health, auth
from src.api.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    app_error_handler,
    unhandled_error_handler,
)
from src.utils.exceptions import AppError
from src.utils.logging import setup_logging


# Initialize logging before anything else
config = get_config()
setup_logging(
    environment=config.environment,
    log_level=config.application.logging.level,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.

    Initializes services on startup and cleans up on shutdown.
    """
    # Startup
    logger.info("application_starting", version="0.1.0")
    services.initialize(config)

    # Health check at startup
    health_status = services.health_check_all()
    for service_name, status in health_status.items():
        if status is not True:
            logger.error("service_health_check_failed", service=service_name, status=status)
            raise RuntimeError(f"Service {service_name} health check failed: {status}")

    logger.info("application_started", services=list(health_status.keys()))
    yield

    # Shutdown
    logger.info("application_shutting_down")
    await services.close_all()
    logger.info("application_stopped")


# Create FastAPI application
app = FastAPI(
    title="braidMgr API",
    description="Multi-tenant RAID log management system",
    version="0.1.0",
    lifespan=lifespan,
)

# =============================================================================
# EXCEPTION HANDLERS
# Convert exceptions to JSON with correlation ID
# =============================================================================
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# =============================================================================
# MIDDLEWARE STACK
# Order matters: middleware runs in reverse order of addition
# 1. CorrelationIdMiddleware runs first (added last)
# 2. RequestLoggingMiddleware runs second (logs with correlation ID)
# 3. CORSMiddleware handles CORS
# =============================================================================
origins = config.application.api.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# =============================================================================
# ROUTES
# =============================================================================
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")

# Future routes will be added here:
# app.include_router(projects.router, prefix="/api/v1")
# app.include_router(items.router, prefix="/api/v1")
