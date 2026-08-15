"""Fail-fast behaviour when narration is systematically broken.

Regression guard for the 2026-08-15 holiday run: a Ctrl+C left the flow method
running in a non-cancellable worker thread, interpreter shutdown made every
subsequent LLM call raise ``RuntimeError: cannot schedule new futures after
shutdown``, and ``generate_fragment`` swallowed all 16 of them. The pipeline
still logged "DOCX written" and clobbered ``output/holiday/itinerary.docx``
with a file containing nothing but placeholders.
"""

from pathlib import Path

import pytest

from epic_news.utils.docx_report import Section, assemble_fragments


class _RaisingLLM:
    def __init__(self, exc: BaseException):
        self.exc = exc
        self.calls = 0

    def call(self, messages):
        self.calls += 1
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


def test_executor_shutdown_aborts_immediately(tmp_path):
    """Shutdown is unrecoverable: abort on the first one, write nothing."""
    llm = _RaisingLLM(RuntimeError("cannot schedule new futures after shutdown"))
    out = tmp_path / "r.docx"

    with pytest.raises(RuntimeError, match="cannot schedule new futures"):
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

    assert llm.calls == 1  # no burning through the remaining sections
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
