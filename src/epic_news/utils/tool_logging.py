#!/usr/bin/env python3
"""
Tool Logging Configuration

This module provides utilities to control tool verbosity and logging
without affecting agent and task verbosity.
"""

import logging
import os

logger = logging.getLogger(__name__)


def configure_tool_logging(mute_tools: bool = True, log_level: str = "WARNING") -> None:
    """
    Configure logging to mute or control tool output.

    Args:
        mute_tools: If True, mute most tool output
        log_level: Logging level for tools (DEBUG, INFO, WARNING, ERROR)
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.WARNING)

    # List of tool loggers to control
    tool_loggers = [
        "crewai.tools",
        "langchain.tools",
        "weasyprint",  # HTML to PDF tool
        "requests",  # HTTP requests from tools
        "urllib3",  # HTTP library
        "serpapi",  # Search tools
        "yfinance",  # Finance tools
        "feedparser",  # RSS tools
    ]

    for logger_name in tool_loggers:
        logger = logging.getLogger(logger_name)
        if mute_tools:
            logger.setLevel(logging.ERROR)  # Only show errors
        else:
            logger.setLevel(numeric_level)

        # Prevent propagation to parent loggers
        logger.propagate = False


def get_quiet_tools_config() -> dict[str, bool]:
    """
    Get configuration for quiet tools based on environment variables.

    Returns:
        Dictionary with tool verbosity settings
    """
    return {
        "verbose": os.getenv("CREWAI_TOOLS_VERBOSE", "false").lower() == "true",
        "mute_requests": os.getenv("MUTE_TOOL_REQUESTS", "true").lower() == "true",
        "mute_search": os.getenv("MUTE_SEARCH_TOOLS", "true").lower() == "true",
    }


def apply_tool_silence() -> None:
    """
    Apply tool silencing based on environment configuration.
    This is the easiest function to call to mute tools.
    """
    config = get_quiet_tools_config()

    # Configure tool logging
    configure_tool_logging(
        mute_tools=not config["verbose"], log_level="ERROR" if not config["verbose"] else "INFO"
    )

    # Set environment variables for tools that check them
    if not config["verbose"]:
        os.environ["LANGCHAIN_VERBOSE"] = "false"
        os.environ["CREWAI_VERBOSE"] = "false"

    logger.info("🔇 Tool output has been muted. Agents and tasks remain verbose.")


# Auto-apply tool silence when module is imported
if __name__ != "__main__":
    # Only auto-apply if not running as script
    if os.getenv("AUTO_MUTE_TOOLS", "true").lower() == "true":
        apply_tool_silence()
