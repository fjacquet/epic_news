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

    Resolution order:
    1. ``EPIC_NEWS_PROJECT_ROOT`` env var (explicit override, e.g. for sandboxed runners).
    2. Walk upward from this file's location until a directory containing
       ``pyproject.toml`` is found — works on every machine and CI runner.
    3. Fall back to the legacy ``~/Projects/crews/epic_news`` if (2) fails
       (kept for backwards compatibility with scripts that monkey-patch
       ``pathlib.Path.home``).

    Raises:
        FileNotFoundError: when no strategy locates a directory containing
        ``pyproject.toml``.
    """
    import os

    # Strategy 1 — explicit override
    override = os.getenv("EPIC_NEWS_PROJECT_ROOT")
    if override:
        candidate = pathlib.Path(override).resolve()
        if (candidate / "pyproject.toml").exists():
            return candidate

    # Strategy 2 — walk up from __file__ looking for pyproject.toml
    current = pathlib.Path(__file__).resolve().parent
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").exists():
            return parent

    # Strategy 3 — legacy fallback
    legacy = (pathlib.Path.home() / "Projects" / "crews" / "epic_news").resolve()
    if (legacy / "pyproject.toml").exists():
        return legacy

    raise FileNotFoundError(
        "Cannot locate project root: no pyproject.toml found via "
        "EPIC_NEWS_PROJECT_ROOT, walking up from path_utils.py, or the "
        "legacy ~/Projects/crews/epic_news location."
    )


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
