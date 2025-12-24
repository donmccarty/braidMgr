"""
Structured logging configuration for braidMgr.

Uses structlog for structured JSON logging in production
and console rendering for development.

Usage:
    from src.utils.logging import setup_logging, get_logger

    # At application startup
    setup_logging(environment="development", log_level="DEBUG")

    # In any module
    logger = get_logger()
    log = logger.bind(project_id=str(project_id))
    log.info("operation_started", operation="create_item")
"""

import logging
import sys
from typing import Optional

import structlog
from structlog.contextvars import merge_contextvars


# =============================================================================
# LOG LEVEL CONFIGURATION BY LAYER
# =============================================================================
# | Layer      | Default Level | What to Log                              |
# |------------|---------------|------------------------------------------|
# | API        | INFO          | Request received, response sent, status  |
# | Middleware | INFO          | Auth success/failure, rate limit hits    |
# | Workflow   | INFO          | Business events, state transitions       |
# | Repository | DEBUG         | Query execution (no sensitive data)      |
# | Service    | DEBUG         | External API calls, retries, timeouts    |
# =============================================================================


def setup_logging(
    environment: str = "development",
    log_level: str = "INFO",
    json_output: Optional[bool] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        environment: "development", "staging", or "production"
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Force JSON output if True, console if False.
                     Defaults to JSON for production, console otherwise.

    Example:
        setup_logging(environment="production", log_level="INFO")
    """
    # Determine output format
    use_json = json_output if json_output is not None else (environment == "production")

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Build processor chain
    # Order matters: earlier processors run first
    processors = [
        # Merge correlation_id and other context from contextvars
        merge_contextvars,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add log level as string
        structlog.processors.add_log_level,
        # Add logger name and function
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        # Format stack traces
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add environment context to all logs
    processors.insert(0, _add_environment_context(environment))

    # Final renderer - JSON for production, console for development
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_environment_context(environment: str):
    """
    Processor that adds environment to all log entries.

    Args:
        environment: Environment name to add

    Returns:
        Structlog processor function
    """

    def processor(logger, method_name, event_dict):
        event_dict["environment"] = environment
        return event_dict

    return processor


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Optional logger name. If not provided, uses calling module name.

    Returns:
        A bound structlog logger instance.

    Example:
        logger = get_logger()
        log = logger.bind(project_id="123")
        log.info("item_created", item_num=42)
    """
    return structlog.get_logger(name)


# =============================================================================
# SENSITIVE DATA PROTECTION
# =============================================================================
# NEVER log:
# - Passwords or tokens
# - SSN (even partial)
# - Financial account numbers
# - API keys or secrets
# =============================================================================


def sanitize_for_logging(data: dict) -> dict:
    """
    Remove or mask sensitive fields from data before logging.

    Args:
        data: Dictionary that may contain sensitive fields.

    Returns:
        Dictionary with sensitive fields masked or removed.

    Example:
        safe_data = sanitize_for_logging({"name": "John", "password": "secret"})
        # Returns: {"name": "John", "password": "***REDACTED***"}
    """
    # Fields to completely redact
    sensitive_fields = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "jwt_secret",
    }

    # Fields to partially mask (show last 4 chars)
    partial_mask_fields = {
        "email",
        "phone",
    }

    result = {}
    for key, value in data.items():
        key_lower = key.lower()

        if key_lower in sensitive_fields:
            result[key] = "***REDACTED***"
        elif key_lower in partial_mask_fields and isinstance(value, str) and len(value) > 4:
            result[key] = f"***{value[-4:]}"
        elif isinstance(value, dict):
            result[key] = sanitize_for_logging(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_for_logging(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result
