"""Fail-fast behaviour when narration is systematically broken.

Regression guard for the 2026-08-15 holiday run: a Ctrl+C left the flow method
running in a non-cancellable worker thread, interpreter shutdown made every
subsequent LLM call raise ``RuntimeError: cannot schedule new futures after
shutdown``, and ``generate_fragment`` swallowed all 16 of them. The pipeline
still logged "DOCX written" and clobbered ``output/holiday/itinerary.docx``
with a file containing nothing but placeholders.
"""

import time
from pathlib import Path

import pytest

from epic_news.utils.docx_report import Section, assemble_fragments


class _RaisingLLM:
    def __init__(self, exc: BaseException, delay: float = 0.0):
        self.exc = exc
        self.delay = delay
        self.calls = 0

    def call(self, messages):
        self.calls += 1
        time.sleep(self.delay)
        raise self.exc


class _FlakyLLM:
    """Fails only for the section whose heading is in ``fail_headings``."""

    def __init__(self, fail_headings: set[str]):
        self.fail_headings = fail_headings

    def call(self, messages):
        heading = messages[1]["content"].split("\n", 1)[0].removeprefix("Section: ")
        if heading in self.fail_headings:
            raise ValueError("provider hiccup")
        return f"## {heading}\n\nprose"


_META = {"title": "T", "author": "Epic News", "date": ""}


def test_executor_shutdown_aborts_immediately(tmp_path, monkeypatch):
    """Shutdown is unrecoverable: abort, stop unstarted sections, write nothing."""
    monkeypatch.setenv("DOCX_FRAGMENT_CONCURRENCY", "2")
    llm = _RaisingLLM(RuntimeError("cannot schedule new futures after shutdown"), delay=0.05)
    out = tmp_path / "r.docx"

    with pytest.raises(RuntimeError, match="cannot schedule new futures"):
        assemble_fragments(
            [Section(f"S{i}", instruction="i", context="c") for i in range(10)],
            _META,
            str(out),
            llm,
            system="sys",
        )

    # Narration is parallel (2 workers): each worker may start one more section before
    # the pool cancels the rest, so at most 2 x workers calls happen.
    assert llm.calls <= 4
    assert not out.exists()


def test_all_narrated_sections_failing_aborts(tmp_path):
    """A report made entirely of placeholders is not a report."""
    llm = _RaisingLLM(ValueError("provider down"))
    out = tmp_path / "r.docx"

    with pytest.raises(RuntimeError, match="placeholder"):
        assemble_fragments(
            [
                Section("Intro", instruction="i", context="c"),
                Section("Budget", instruction="i", context="c"),
            ],
            _META,
            str(out),
            llm,
            system="sys",
        )

    assert not out.exists()


def test_partial_failure_still_degrades_gracefully(tmp_path):
    """One bad section must not discard the whole run."""
    llm = _FlakyLLM({"Budget"})
    out = tmp_path / "r.docx"

    assemble_fragments(
        [
            Section("Intro", instruction="i", context="c"),
            Section("Budget", instruction="i", context="c"),
        ],
        _META,
        str(out),
        llm,
        system="sys",
    )

    assert Path(out).exists()


def test_deterministic_sections_are_not_counted_as_narration(tmp_path):
    """A deck of verbatim bodies plus one failed narration is still publishable."""
    llm = _RaisingLLM(ValueError("provider down"))
    out = tmp_path / "r.docx"

    assemble_fragments(
        [
            Section("Prix", body="| A | 9.90 |"),
            Section("Intro", instruction="i", context="c"),
        ],
        _META,
        str(out),
        llm,
        system="sys",
    )

    assert Path(out).exists()
