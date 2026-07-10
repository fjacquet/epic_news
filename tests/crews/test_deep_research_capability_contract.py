"""deep_research agents must not be asked to do what their tools cannot do.

Two production failures came from this mismatch:

* data_analyst was told to save and run Python scripts. CrewAI removed
  CodeInterpreterTool, so it held only a read-only FileReadTool and called it on the
  target *directory* -- "File not found: output/deep_research/python_scripts".
* information_collector was told to save its corpus as markdown files. It has no
  file-writer, so data_analyst later invented filenames and tried to read a corpus
  nobody had written -- "File not found: .../crewai_documentation_v1.15.2.md".

These tests pin the contract: no task may promise file writes or code execution, and
data_analyst stays tool-less so it cannot invent paths to read.
"""

from pathlib import Path

import pytest
import yaml

CONFIG = Path(__file__).resolve().parents[2] / "src/epic_news/crews/deep_research/config"


@pytest.fixture(scope="module")
def tasks() -> dict:
    return yaml.safe_load((CONFIG / "tasks.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def agents() -> dict:
    return yaml.safe_load((CONFIG / "agents.yaml").read_text(encoding="utf-8"))


def _task_text(task: dict) -> str:
    return f"{task.get('description', '')}\n{task.get('expected_output', '')}"


def test_no_task_instructs_writing_files_into_the_output_dir(tasks):
    """No agent here can write files; a task must not claim otherwise.

    `output_file:` is fine -- CrewAI writes that itself.
    """
    offenders = []
    for name, task in tasks.items():
        text = _task_text(task)
        if 'dans des fichiers markdown dans "output' in text or "python_scripts" in text:
            offenders.append(name)

    assert not offenders, f"tasks promise file writes no agent can perform: {offenders}"


def test_no_task_instructs_code_execution(tasks):
    """CrewAI removed CodeInterpreterTool; nothing may promise to run code."""
    banned = ("interpréteur de code", "uv run python", "pip install")
    offenders = [n for n, t in tasks.items() if any(b in _task_text(t).lower() for b in banned)]

    assert not offenders, f"tasks instruct code execution that cannot happen: {offenders}"


def test_agents_yaml_declares_no_deprecated_execution_flags(agents):
    for name, cfg in agents.items():
        assert "allow_code_execution" not in cfg, f"{name} sets a deprecated no-op flag"
        assert "code_execution_mode" not in cfg, f"{name} sets a deprecated no-op flag"


def test_agents_yaml_declares_no_tools(agents):
    """Tools are assigned in Python, never YAML (project convention)."""
    for name, cfg in agents.items():
        assert "tools" not in cfg, f"{name} declares tools in YAML"


def test_data_analyst_is_tool_less():
    """Given any file tool it invents filenames; its corpus arrives via context."""
    from epic_news.crews.deep_research.deep_research import DeepResearchCrew

    analyst = DeepResearchCrew().data_analyst()

    assert analyst.tools == [], f"data_analyst must hold no tools, got {[t.name for t in analyst.tools]}"
    assert not analyst.allow_code_execution
