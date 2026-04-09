# ADR-004: Flow-Based Orchestration with ReceptionFlow

## Status

Accepted

## Context

With 24+ specialized crews, the application needed a centralized dispatch mechanism that could classify user requests, route them to the correct crew, and handle results uniformly. Direct crew invocation would require each entry point (CLI, API, Streamlit) to duplicate routing logic.

## Decision

- Use CrewAI's `Flow` class with `@start`, `@router`, and `@listen` decorators for orchestration
- Implement a single `ReceptionFlow` class in `main.py` as the sole entry point
- Each crew has a dedicated `generate_*()` method decorated with `@listen`
- Request classification happens via the `classify` crew, which returns a crew identifier
- All entry points (CLI via `crewai flow kickoff`, FastAPI, Streamlit) call `ReceptionFlow`

## Consequences

- Single point of control for all crew dispatch logic
- Adding a new crew requires only: crew implementation + one `generate_*()` method in ReceptionFlow
- Classification errors are isolated to the classify crew, not scattered across entry points
- `main.py` grows with each crew (~72 KB currently) but remains the single source of truth
- Async support available via `@listen` decorator for concurrent crew execution
