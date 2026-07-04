"""Regression tests for CrewAI 1.15+ async-task / agent-executor isolation.

CrewAI 1.15 changed ``Agent`` so that each agent owns a single, stateful
``AgentExecutor`` guarded by an ``_is_executing`` flag. When several
``async_execution=True`` tasks are bound to the *same* agent instance, the crew
runs them concurrently and the second concurrent ``agent_executor.invoke()``
raises::

    RuntimeError: Executor is already running.
                  Cannot invoke the same executor instance concurrently.

The fix is to give every task in a concurrent (consecutive-async) batch its own
agent instance (via ``Agent.copy()``). These tests lock in that invariant:

1. Every crew that uses async tasks must build without error.
2. Within any batch of consecutive async tasks (the unit CrewAI runs in
   parallel), no two tasks may share the same agent object.
"""

from __future__ import annotations

import pytest

from tests.crews._registry import ASYNC_CREW_CLASSES, build_crew


def _concurrent_async_batches(tasks):
    """Split tasks into the batches CrewAI runs concurrently.

    CrewAI's sequential process accumulates consecutive ``async_execution`` tasks
    and flushes them together when it reaches a synchronous task. Each such run
    of consecutive async tasks is one concurrency batch.
    """
    batches: list[list] = []
    current: list = []
    for task in tasks:
        if getattr(task, "async_execution", False):
            current.append(task)
        elif current:
            batches.append(current)
            current = []
    if current:
        batches.append(current)
    return batches


@pytest.mark.parametrize("crew_cls", ASYNC_CREW_CLASSES, ids=lambda c: c.__name__)
def test_async_crew_builds_with_distinct_agents(crew_cls):
    """Every async-using crew must construct without raising, and no two
    tasks in a concurrent async batch may share an agent instance."""
    crew = build_crew(crew_cls)
    assert crew.tasks, f"{crew_cls.__name__}: crew built with no tasks"

    for batch in _concurrent_async_batches(crew.tasks):
        agent_ids = [id(t.agent) for t in batch if t.agent is not None]
        assert len(agent_ids) == len(set(agent_ids)), (
            f"{crew_cls.__name__}: {len(agent_ids) - len(set(agent_ids))} async task(s) in a "
            f"concurrent batch share an agent instance; each concurrent async task "
            f"needs its own agent (use Agent.copy()) to avoid "
            f"'Executor is already running' under CrewAI 1.15+."
        )
