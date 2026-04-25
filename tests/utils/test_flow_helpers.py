"""Unit tests for epic_news.utils.flow_helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from epic_news.utils.flow_helpers import load_or_parse_model, render_and_write_html


class _DummyModel(BaseModel):
    name: str
    value: int = 0


def test_load_or_parse_model_from_valid_json(tmp_path: Path):
    json_file = tmp_path / "ok.json"
    json_file.write_text('{"name": "alice", "value": 42}', encoding="utf-8")

    model = load_or_parse_model(json_file, _DummyModel, fallback_output=None, label="dummy")

    assert model.name == "alice"
    assert model.value == 42


def test_load_or_parse_model_falls_back_on_missing_file(tmp_path: Path):
    missing = tmp_path / "missing.json"
    fallback = SimpleNamespace(raw='{"name": "bob", "value": 7}')

    model = load_or_parse_model(missing, _DummyModel, fallback_output=fallback)

    assert model.name == "bob"
    assert model.value == 7


def test_load_or_parse_model_falls_back_on_invalid_json(tmp_path: Path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not valid json", encoding="utf-8")
    fallback = SimpleNamespace(raw='{"name": "carol", "value": 3}')

    model = load_or_parse_model(broken, _DummyModel, fallback_output=fallback)

    assert model.name == "carol"


def test_load_or_parse_model_falls_back_on_validation_error(tmp_path: Path):
    # JSON parses but does not match the schema → ValidationError → fallback.
    mismatched = tmp_path / "mismatched.json"
    mismatched.write_text('{"unexpected": "field"}', encoding="utf-8")
    fallback = SimpleNamespace(raw='{"name": "dan", "value": 1}')

    model = load_or_parse_model(mismatched, _DummyModel, fallback_output=fallback)

    assert model.name == "dan"


def test_load_or_parse_model_raises_when_fallback_has_no_raw(tmp_path: Path):
    missing = tmp_path / "nope.json"
    fallback = SimpleNamespace(raw="")

    with pytest.raises(ValueError):
        load_or_parse_model(missing, _DummyModel, fallback_output=fallback)


def test_load_or_parse_model_accepts_str_path(tmp_path: Path):
    """str path should work the same as Path."""
    json_file = tmp_path / "ok.json"
    json_file.write_text('{"name": "alice", "value": 42}', encoding="utf-8")

    model = load_or_parse_model(str(json_file), _DummyModel, fallback_output=None)

    assert model.name == "alice"


def test_load_or_parse_model_handles_empty_label(tmp_path: Path):
    """Empty label is accepted without error and the model still loads."""
    json_file = tmp_path / "ok.json"
    json_file.write_text('{"name": "x", "value": 1}', encoding="utf-8")

    model = load_or_parse_model(json_file, _DummyModel, fallback_output=None, label="")

    assert model.name == "x"
    assert model.value == 1


def test_render_and_write_html_creates_parent_dir_and_writes(tmp_path: Path, monkeypatch):
    # Stub TemplateManager.render_report to avoid loading real templates.
    from epic_news.utils import flow_helpers

    def _fake_render(self, selected_crew, content_data):
        return f"<html>{selected_crew}:{content_data['name']}</html>"

    monkeypatch.setattr(flow_helpers.TemplateManager, "render_report", _fake_render)

    target = tmp_path / "nested" / "deep" / "report.html"
    result = render_and_write_html("POEM", _DummyModel(name="eve", value=1), target)

    assert result == target
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "<html>POEM:eve</html>"
