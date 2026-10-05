"""Crew modules stay in CrewAI's documented form and are checked by the ADR-014 guard."""

import ast
import os
import subprocess
import sys
from pathlib import Path

CREWS = Path(__file__).resolve().parents[2] / "src" / "epic_news" / "crews"
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


def test_no_crew_module_calls_load_dotenv():
    offenders = [str(p) for p in CREW_MODULES if "load_dotenv" in p.read_text(encoding="utf-8")]
    assert offenders == []


def test_crew_imported_alone_still_sees_dotenv(tmp_path):
    # Entry points load .env; a crew imported on its own gets it through LLMConfig's module.
    (tmp_path / ".env").write_text("MODEL=gemini/probe-model\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "MODEL"}
    code = "import os\nimport epic_news.crews.poem.poem_crew\nprint(os.environ.get('MODEL'))\n"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    assert result.stdout.strip().splitlines()[-1] == "gemini/probe-model"
