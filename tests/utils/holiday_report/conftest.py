import pytest


@pytest.fixture(autouse=True)
def _cwd_in_tmp(tmp_path, monkeypatch):
    """build_docx only writes under ./output/ (ADR-015): run each test from its tmp dir."""
    monkeypatch.chdir(tmp_path)
