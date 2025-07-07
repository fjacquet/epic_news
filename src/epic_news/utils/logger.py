"""
Logging configuration for epic_news application.

This module provides a centralized logging configuration for the entire epic_news
application using Loguru.
"""

import os
import sys
from pathlib import Path

from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
    app_name: str = "epic_news",
) -> None:
    """
    Set up Loguru logging configuration for the application.

    Args:
        log_level: The logging level to use (default: "INFO")
        log_to_file: Whether to log to file (default: True)
        log_dir: Directory to store log files (default: "logs")
        app_name: Name of the application for log files (default: "epic_news")
    """
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(sys.stdout, level=log_level.upper())

    if log_to_file:
        Path(log_dir).mkdir(exist_ok=True)
        log_file = os.path.join(log_dir, f"{app_name}.log")
        error_log_file = os.path.join(log_dir, f"{app_name}_error.log")

        # Add file handlers
        logger.add(
            log_file,
            level=log_level.upper(),
            rotation="10 MB",
            retention="30 days",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        logger.add(
            error_log_file,
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )


def get_logger(name: str, log_level: str | None = None) -> "logger":
    """
    Get a logger with the given name.

    Args:
        name: The name of the logger (usually __name__)
        log_level: Optional specific log level for this logger

    Returns:
        A Loguru logger instance
    """
    if log_level:
        logger.configure(handlers=[{"sink": sys.stdout, "level": log_level.upper()}])
    return logger.bind(name=name)
