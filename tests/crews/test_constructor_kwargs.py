"""Agent/Task/Crew constructors in src must only receive kwargs CrewAI declares.

CrewAI's pydantic models silently drop unknown keyword arguments, so a misspelled or
non-existent setting (``llm_timeout=``, ``Crew(max_iter=...)``, ``Task(verbose=...)``)
looks configured but never applies. This test parses the source with ``ast`` and checks
every keyword passed to an ``Agent(``, ``Task(`` or ``Crew(`` call against the model's
declared fields (and their aliases).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from crewai import Agent, Crew, Task

SRC = Path(__file__).resolve().parents[2] / "src" / "epic_news"
MODELS = {"Agent": Agent, "Task": Task, "Crew": Crew}


def _allowed_kwargs(model) -> set[str]:
    allowed: set[str] = set()
    for name, field in model.model_fields.items():
        allowed.add(name)
        if field.alias:
            allowed.add(field.alias)
    return allowed


def _constructor_calls():
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in MODELS:
                yield path, node


def test_scan_finds_constructor_calls():
    """Guard against the scan silently matching nothing."""
    found = {node.func.id for _, node in _constructor_calls()}
    assert found == set(MODELS)


@pytest.mark.parametrize("name", sorted(MODELS))
def test_constructor_kwargs_are_declared_fields(name):
    allowed = _allowed_kwargs(MODELS[name])
    offenders = []
    for path, node in _constructor_calls():
        if node.func.id != name:
            continue
        for kw in node.keywords:
            if kw.arg is not None and kw.arg not in allowed:
                offenders.append(f"{path.relative_to(SRC)}:{kw.lineno} {name}({kw.arg}=...)")
    assert not offenders, f"{name}() receives kwargs CrewAI does not declare (silently dropped): {offenders}"
