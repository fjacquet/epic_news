# ADR-002: Implementation of CrewAI Scoped Memory

## Status

Accepted

## Context

Crews using `memory=True` share a single flat memory space. As crews grow in complexity (e.g., `fin_daily` with 3 agents and 7 tasks), token usage explodes because every agent retrieves all memories from all other agents.

## Decision

- Use CrewAI's `Memory` class with `memory.scope("/agent/<name>")` for per-agent private scopes
- Centralize memory configuration via `LLMConfig.get_memory_config()` factory
- Configure scoring weights: recency=0.4, semantic=0.4, importance=0.2
- Set `query_analysis_threshold=200` to skip LLM analysis for short queries
- Use `text-embedding-3-small` as embedder
- Roll out progressively: `fin_daily` and `meeting_prep` first

## Consequences

- Reduced token usage per crew execution (agents only see their own scope)
- Centralized, consistent memory config across all crews
- Easy to extend to additional crews by importing `LLMConfig.get_memory_config()`
- Cross-scope access available via `memory.slice()` if needed later
