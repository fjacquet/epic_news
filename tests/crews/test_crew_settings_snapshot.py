# tests/crews/test_crew_settings_snapshot.py
"""Characterisation snapshot: every crew's agents, tasks and crew settings.

Simplification S1 must not change any of these. Regenerate only on purpose:
    UPDATE_CREW_SNAPSHOT=1 env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_settings_snapshot.py
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

from tests.crews._registry import ALL_CREW_CLASSES

SNAPSHOT = Path(__file__).parent / "snapshots" / "crew_settings.json"
_MCP_MODULES = ("epic_news.crews.pestel.pestel_crew", "epic_news.crews.deep_research.deep_research")


def _digest(text: object) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def _agent_settings(agent, index_of) -> dict:
    llm = agent.llm
    return {
        "id": index_of(agent),
        "role": agent.role,
        "goal": _digest(agent.goal),
        "backstory": _digest(agent.backstory),
        "model": getattr(llm, "model", None),
        "timeout": getattr(llm, "timeout", None),
        "max_iter": agent.max_iter,
        "max_rpm": agent.max_rpm,
        "max_retry_limit": agent.max_retry_limit,
        "allow_delegation": agent.allow_delegation,
        "respect_context_window": agent.respect_context_window,
        "verbose": agent.verbose,
        "system_template": _digest(agent.system_template),
        "tools": sorted(tool.name for tool in agent.tools or []),
    }


def crew_settings(crew_cls, monkeypatch) -> dict:
    # Pin the model: .env (local) and the test default (CI) differ.
    monkeypatch.setenv("MODEL", "openrouter/test/model")
    # get_github_tools() returns [] without a token; CI has none, local .env may.
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    # MCP servers must not change the snapshot (their tools depend on the machine).
    for module in _MCP_MODULES:
        monkeypatch.setattr(f"{module}.get_mcp_tools_or_empty", lambda crew: [])
    crew = crew_cls().crew()
    ids: dict[int, int] = {}

    def index_of(agent) -> int:
        return ids.setdefault(id(agent), len(ids))

    agents = [_agent_settings(a, index_of) for a in crew.agents]
    tasks = [
        {
            "name": t.name,
            "description": _digest(t.description),
            "expected_output": _digest(t.expected_output),
            "agent": index_of(t.agent) if t.agent is not None else None,
            "context": [c.name for c in t.context] if isinstance(t.context, list) else None,
            "async_execution": t.async_execution,
            "output_pydantic": t.output_pydantic.__name__ if t.output_pydantic else None,
            "output_file": t.output_file,
        }
        for t in crew.tasks
    ]
    return {
        "process": str(crew.process),
        "max_rpm": crew.max_rpm,
        "verbose": crew.verbose,
        "agents": agents,
        "tasks": tasks,
    }


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_crew_settings_match_snapshot(crew_cls, monkeypatch):
    current = crew_settings(crew_cls, monkeypatch)
    stored = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    if os.getenv("UPDATE_CREW_SNAPSHOT") == "1":
        stored[crew_cls.__name__] = current
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(
            json.dumps(stored, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return
    assert crew_cls.__name__ in stored, (
        f"No snapshot for {crew_cls.__name__}; run with UPDATE_CREW_SNAPSHOT=1"
    )
    assert current == stored[crew_cls.__name__]
