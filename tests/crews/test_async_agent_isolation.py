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

import importlib
import os

import pytest

# LLMConfig builds an LLM object without calling the API, but a key must exist.
os.environ.setdefault("OPENROUTER_API_KEY", "sk-dummy-key-for-tests")
os.environ.setdefault("MODEL", "openrouter/mistralai/mistral-small-2603")

# (crew label, module path, class name) for every crew that uses async_execution.
ASYNC_CREWS: list[tuple[str, str, str]] = [
    ("meeting_prep", "epic_news.crews.meeting_prep.meeting_prep_crew", "MeetingPrepCrew"),
    ("sales_prospecting", "epic_news.crews.sales_prospecting.sales_prospecting_crew", "SalesProspectingCrew"),
    (
        "geospatial_analysis",
        "epic_news.crews.geospatial_analysis.geospatial_analysis_crew",
        "GeospatialAnalysisCrew",
    ),
    ("company_profiler", "epic_news.crews.company_profiler.company_profiler_crew", "CompanyProfilerCrew"),
    ("news_daily", "epic_news.crews.news_daily.news_daily", "NewsDailyCrew"),
    ("pestel", "epic_news.crews.pestel.pestel_crew", "PestelCrew"),
    ("legal_analysis", "epic_news.crews.legal_analysis.legal_analysis_crew", "LegalAnalysisCrew"),
    ("fin_daily", "epic_news.crews.fin_daily.fin_daily", "FinDailyCrew"),
    (
        "cross_reference_report",
        "epic_news.crews.cross_reference_report_crew.cross_reference_report_crew",
        "CrossReferenceReportCrew",
    ),
    ("web_presence", "epic_news.crews.web_presence.web_presence_crew", "WebPresenceCrew"),
    ("holiday_planner", "epic_news.crews.holiday_planner.holiday_planner_crew", "HolidayPlannerCrew"),
    ("tech_stack", "epic_news.crews.tech_stack.tech_stack_crew", "TechStackCrew"),
    ("hr_intelligence", "epic_news.crews.hr_intelligence.hr_intelligence_crew", "HRIntelligenceCrew"),
]


def _build_crew(module_path: str, class_name: str):
    module = importlib.import_module(module_path)
    crew_cls = getattr(module, class_name)
    return crew_cls().crew()


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


@pytest.mark.parametrize("label,module_path,class_name", ASYNC_CREWS, ids=[c[0] for c in ASYNC_CREWS])
def test_crew_builds(label: str, module_path: str, class_name: str):
    """Every async-using crew must construct without raising."""
    crew = _build_crew(module_path, class_name)
    assert crew.tasks, f"{label}: crew built with no tasks"


@pytest.mark.parametrize("label,module_path,class_name", ASYNC_CREWS, ids=[c[0] for c in ASYNC_CREWS])
def test_concurrent_async_tasks_have_distinct_agents(label: str, module_path: str, class_name: str):
    """No two tasks in a concurrent async batch may share an agent instance."""
    crew = _build_crew(module_path, class_name)
    for batch in _concurrent_async_batches(crew.tasks):
        agent_ids = [id(t.agent) for t in batch if t.agent is not None]
        assert len(agent_ids) == len(set(agent_ids)), (
            f"{label}: {len(agent_ids) - len(set(agent_ids))} async task(s) in a "
            f"concurrent batch share an agent instance; each concurrent async task "
            f"needs its own agent (use Agent.copy()) to avoid "
            f"'Executor is already running' under CrewAI 1.15+."
        )
