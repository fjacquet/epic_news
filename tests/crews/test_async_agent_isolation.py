"""Crew tasks run sequentially; concurrent async execution is not safe on CrewAI 1.15+.

Two independent failure modes bite when several ``async_execution=True`` tasks run in
the same concurrency batch:

1. **Shared executor.** CrewAI 1.15 gives each ``Agent`` a single stateful
   ``AgentExecutor`` guarded by ``_is_executing``. Two concurrent tasks bound to the
   same agent instance raise::

       RuntimeError: Executor is already running.
                     Cannot invoke the same executor instance concurrently.

   Mitigable per-task with ``Agent.copy()``, which several crews used to do.

2. **Tool call leaking into TaskOutput.raw.** The concurrent path returns the
   provider's raw ``tool_calls`` list where a ``str`` is expected, killing the crew
   with ``ValidationError: Input should be a valid string``. First seen in
   HolidayPlannerCrew; the ``acall`` wrapper in ``epic_news.config.llm_config`` now
   absorbs it, but running sequentially removes the trigger entirely.

So every crew declares ``async_execution=False``. These tests lock that in and keep the
per-batch agent-isolation invariant enforced should async ever be re-introduced.
"""

from __future__ import annotations

import pytest

from tests.crews._registry import ALL_CREW_CLASSES, build_crew


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


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_crew_declares_no_async_tasks(crew_cls):
    """No crew may opt into concurrent async execution (see module docstring).

    Asserted on the built ``Task`` objects rather than the source text, so a task that
    picks up ``async_execution`` from its YAML config is caught too.
    """
    crew = build_crew(crew_cls)
    async_tasks = [t.name or t.description[:60] for t in crew.tasks if getattr(t, "async_execution", False)]
    assert not async_tasks, (
        f"{crew_cls.__name__} has async_execution=True on: {async_tasks}. Concurrent "
        f"async tasks are unsafe on CrewAI 1.15+: they share one AgentExecutor and can "
        f"leak a raw tool_calls list into TaskOutput.raw. Use async_execution=False."
    )


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_async_crew_builds_with_distinct_agents(crew_cls):
    """Should async ever return: no two tasks in a concurrent batch may share an agent."""
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
