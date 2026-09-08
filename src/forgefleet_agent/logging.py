"""Structured logging configuration for ForgeFleet Agent."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

import structlog

from .config import settings


def setup_logging() -> None:
    """Configure structured logging."""
    settings.ensure_directories()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if settings.log_format == "structured"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # File handler with rotation
    log_file = settings.log_path / "forgefleet_agent.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=settings.log_max_size_mb * 1024 * 1024,
        backupCount=settings.log_backup_count,
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(name)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str = __name__) -> Any:
    """Get a structured logger."""
    return structlog.get_logger(name)
