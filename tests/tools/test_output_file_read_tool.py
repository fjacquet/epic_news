"""OutputFileReadTool must only read files inside its root (``output/`` by default)."""

import json
import os

import pytest

from epic_news.tools.output_file_read_tool import MAX_CHARS, OutputFileReadTool


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Run in a temp CWD with an output/ dir and a secret file outside it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "osint").mkdir(parents=True)
    (tmp_path / "output" / "osint" / "report.json").write_text('{"k": "v"}', encoding="utf-8")
    (tmp_path / "secret.env").write_text("API_KEY=xyz", encoding="utf-8")
    return tmp_path


def _run(tool, path) -> dict:
    return json.loads(tool.run(file_path=str(path)))


def test_reads_file_inside_output(workdir):
    result = _run(OutputFileReadTool(), "output/osint/report.json")
    assert result == {"content": '{"k": "v"}'}


def test_reads_absolute_path_inside_output(workdir):
    result = _run(OutputFileReadTool(), workdir / "output" / "osint" / "report.json")
    assert result["content"] == '{"k": "v"}'


def test_refuses_relative_traversal(workdir):
    result = _run(OutputFileReadTool(), "output/../secret.env")
    assert "error" in result
    assert "API_KEY" not in json.dumps(result)


def test_refuses_absolute_path_outside_output(workdir):
    result = _run(OutputFileReadTool(), workdir / "secret.env")
    assert "error" in result
    assert "API_KEY" not in json.dumps(result)


def test_refuses_symlink_escaping_output(workdir):
    os.symlink(workdir / "secret.env", workdir / "output" / "link.env")
    result = _run(OutputFileReadTool(), "output/link.env")
    assert "error" in result
    assert "API_KEY" not in json.dumps(result)


def test_missing_file_returns_error(workdir):
    result = _run(OutputFileReadTool(), "output/nope.json")
    assert "error" in result


def test_directory_returns_error(workdir):
    result = _run(OutputFileReadTool(), "output/osint")
    assert "error" in result


def test_caps_content_size(workdir):
    (workdir / "output" / "big.txt").write_text("x" * (MAX_CHARS + 10), encoding="utf-8")
    result = _run(OutputFileReadTool(), "output/big.txt")
    assert len(result["content"]) == MAX_CHARS
    assert result["truncated"] is True


def test_custom_root(workdir):
    (workdir / "data").mkdir()
    (workdir / "data" / "stock.csv").write_text("Name,Ticker\n", encoding="utf-8")
    tool = OutputFileReadTool(root="data")
    assert _run(tool, workdir / "data" / "stock.csv")["content"] == "Name,Ticker\n"
    assert "error" in _run(tool, "output/osint/report.json")
