# ADR-010: UV as Exclusive Package Manager

## Status

Accepted

## Context

Python package management options include pip, poetry, pdm, and uv. The project has 100+ dependencies including ML libraries, web frameworks, and financial data tools. Installation speed and reproducibility matter for both local development and CI.

## Decision

- Use `uv` exclusively for all package management operations
- `uv sync && uv pip install -e .` for environment setup
- `uv add` / `uv remove` for dependency changes
- `uv run` prefix for all tool execution (pytest, ruff, mypy, pre-commit)
- `uv.lock` committed for reproducible builds
- pip, poetry, and other managers are explicitly forbidden (documented in CLAUDE.md)

## Consequences

- 10-100x faster dependency resolution compared to pip/poetry
- Reproducible builds via lockfile
- Single tool for environment management, dependency resolution, and script execution
- All Makefile targets and CI workflows use `uv run` consistently
- Developers must install `uv` — not available via pip itself
