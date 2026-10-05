"""Shared setup for flow e2e tests: isolate cwd and gate email off."""

import pytest


@pytest.fixture(autouse=True)
def _flow_sandbox(tmp_path, monkeypatch):
    """Run each flow test in an isolated cwd with email disabled."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")
