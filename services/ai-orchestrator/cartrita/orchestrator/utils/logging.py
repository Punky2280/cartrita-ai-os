# Cartrita AI OS - Logging Configuration
# Structured Logging with OpenTelemetry Integration

"""
Advanced logging configuration for Cartrita AI OS.
Implements structured logging with OpenTelemetry integration.
"""

import logging
import sys
from pathlib import Path

import structlog

from cartrita.orchestrator.utils.config import settings


def setup_logging(
    level: str | None = None,
    format_type: str | None = None,
    log_file: Path | None = None,
) -> None:
    """Setup comprehensive logging configuration."""

    # Use settings if not provided
    level = level or settings.monitoring.log_level
    format_type = format_type or settings.monitoring.log_format
    log_file = log_file or settings.monitoring.log_file

    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    # Configure structlog
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if format_type == "json":
        # JSON logging for production
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable logging for development
        shared_processors.extend(
            [
                structlog.processors.ExceptionPrettyPrinter(),
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure loguru for application logging
    from loguru import logger as loguru_logger

    # Remove default handler
    loguru_logger.remove()

    # Add console handler
    if format_type == "json":
        loguru_logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=level.upper(),
            serialize=True,
        )
    else:
        loguru_logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level.upper(),
            colorize=True,
            serialize=False,
        )

    # Add file handler if specified
    if log_file:
        loguru_logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=level.upper(),
            rotation="10 MB",
            retention="1 week",
            serialize=(format_type == "json"),
        )

    # Configure third-party loggers
    _configure_third_party_loggers(level)


def _configure_third_party_loggers(level: str) -> None:
    """Configure logging for third-party libraries."""

    # FastAPI
    logging.getLogger("fastapi").setLevel(getattr(logging, level.upper()))
    logging.getLogger("uvicorn").setLevel(getattr(logging, level.upper()))
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Database
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # AI/ML libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)

    # HTTP clients
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    # OpenTelemetry
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry.sdk").setLevel(logging.WARNING)

    # Redis
    logging.getLogger("redis").setLevel(logging.WARNING)

    # Vector databases
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Global logger instance
logger = get_logger(__name__)
