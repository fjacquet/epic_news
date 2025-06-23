"""Centralized path management utilities for epic_news crews.

This module provides standardized path calculation functions to ensure
all crews use consistent, correct output directory paths and prevent
the creation of nested /Users/.../Users/... directory structures.

Design Principles:
- All output paths must be relative to project root
- No nested user directory structures allowed
- Single source of truth for path calculations
- Validation to prevent path misuse
"""

from __future__ import annotations

import pathlib


def get_project_root() -> pathlib.Path:
    """Get the absolute path to the project root directory.

    This function returns the canonical project root path, ensuring no nested Users directories.

    Returns:
        pathlib.Path: Absolute path to the project root directory
    """
    # CRITICAL FIX: Always use this hardcoded path pattern to avoid any nested paths
    # Extract the user home directory and ensure we construct a clean path
    home_dir = pathlib.Path.home()

    # The project is always at ~/Projects/crews/epic_news or equivalent
    project_root = home_dir / "Projects" / "crews" / "epic_news"

    # Final sanity check - this can't be wrong
    if not (project_root / "pyproject.toml").exists():
        raise FileNotFoundError(f"Cannot locate project root at expected location: {project_root}")

    # Get canonical path without any duplicate /Users/ segments
    clean_path = project_root.resolve()

    # Extra validation to prevent pathological paths
    path_str = str(clean_path)
    if path_str.count("Users") > 1:
        raise ValueError(f"Invalid nested Users in path: {path_str}")

    return clean_path


def validate_output_path(path: str) -> None:
    """Validate that an output path follows project design principles.

    This function enforces the critical constraint that output paths
    must never create nested /Users/.../Users/... directory structures.

    Args:
        path: The path to validate

    Raises:
        ValueError: If the path violates design principles
    """
    if not path:
        raise ValueError("Output path cannot be empty")

    # Check for nested /Users/ directories (critical bug prevention)
    if "/Users/" in path and path.count("/Users/") > 1:
        raise ValueError(
            f"Invalid output path: '{path}'\n"
            "Detected nested /Users/.../Users/... directory structure.\n"
            "This violates project design principles. Paths must be relative to project root only."
        )

    # Ensure path is within project structure
    project_root = get_project_root()
    try:
        # Convert to absolute path and check if it's within project
        abs_path = pathlib.Path(path).resolve()
        abs_path.relative_to(project_root)
    except (ValueError, OSError):
        raise ValueError(
            f"Output path '{path}' is outside the project directory.\n"
            f"All outputs must be within: {project_root}"
        )


def get_template_dir() -> str:
    """Get the absolute path to the templates directory.

    Returns:
        str: Absolute path to the templates directory
    """
    project_root = get_project_root()
    template_dir = project_root / "templates"
    return str(template_dir)
