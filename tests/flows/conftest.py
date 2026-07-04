"""Shared setup for flow e2e tests: isolate cwd and gate email off."""

import pytest

from epic_news.utils.observability import TRACE_DIR


@pytest.fixture(autouse=True)
def _flow_sandbox(tmp_path, monkeypatch):
    """Run each flow test in an isolated cwd with email disabled.

    observability creates TRACE_DIR at import time relative to the original
    cwd, so it must be recreated inside the per-test cwd.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")
    (tmp_path / TRACE_DIR).mkdir()
