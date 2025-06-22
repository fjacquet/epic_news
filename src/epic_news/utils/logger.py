"""
Logging configuration for epic_news application.

This module provides a centralized logging configuration for the entire epic_news
application. It includes configurations for console and file logging with
different log levels, formatters, and handlers.

Usage:
    from epic_news.utils.logger import get_logger # Updated path

    # Get logger for a specific module
    logger = get_logger(__name__)

    # Use the logger
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "logs",
    app_name: str = "epic_news",
) -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_level: The logging level to use (default: logging.INFO)
        log_to_file: Whether to log to file (default: True)
        log_dir: Directory to store log files (default: "logs")
        app_name: Name of the application for log files (default: "epic_news")

    """
    # Create logs directory if it doesn't exist
    if log_to_file:
        Path(log_dir).mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatters
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_formatter = logging.Formatter(console_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)

    # Add console handler to root logger
    root_logger.addHandler(console_handler)

    # Add file handler if requested
    if log_to_file:
        # Daily rotating file handler
        log_file = os.path.join(log_dir, f"{app_name}.log")
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            backupCount=30,  # Keep logs for 30 days
        )
        file_handler.setLevel(log_level)

        # More detailed format for file logs
        file_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
        file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)

        # Add file handler to root logger
        root_logger.addHandler(file_handler)

        # Create error log file handler (for ERROR and above)
        error_log_file = os.path.join(log_dir, f"{app_name}_error.log")
        error_file_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(file_formatter)

        # Add error file handler to root logger
        root_logger.addHandler(error_file_handler)


def get_logger(name: str, log_level: int | None = None) -> logging.Logger:  # noqa: UP007
    """
    Get a logger with the given name.

    Args:
        name: The name of the logger (usually __name__)
        log_level: Optional specific log level for this logger

    Returns:
        logging.Logger: Configured logger instance

    """
    logger = logging.getLogger(name)

    if log_level is not None:
        logger.setLevel(log_level)

    return logger
