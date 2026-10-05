"""Crew modules stay in CrewAI's documented form and are checked by the ADR-014 guard."""

import ast
from pathlib import Path

CREWS = Path("src/epic_news/crews")
CREW_MODULES = sorted(p for p in CREWS.rglob("*.py") if p.name != "__init__.py")


def _literal_calls(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"Agent", "Task", "Crew"}
    }


def test_every_crew_module_builds_agents_tasks_and_crews_literally():
    # mypy's call-arg check is off for epic_news.crews.* (CrewAI's Task(config=...) is untypable);
    # test_constructor_kwargs.py scans these literal calls for unknown kwargs instead.
    crew_files = [p for p in CREW_MODULES if "@CrewBase" in p.read_text(encoding="utf-8")]
    assert len(crew_files) == 24
    for path in crew_files:
        assert {"Agent", "Task", "Crew"} <= _literal_calls(path), path
