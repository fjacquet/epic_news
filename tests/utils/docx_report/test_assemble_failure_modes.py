"""Fail-fast behaviour when narration is systematically broken.

Regression guard for the 2026-08-15 holiday run: a Ctrl+C left the flow method
running in a non-cancellable worker thread, interpreter shutdown made every
subsequent LLM call raise ``RuntimeError: cannot schedule new futures after
shutdown``, and ``generate_fragment`` swallowed all 16 of them. The pipeline
still logged "DOCX written" and clobbered ``output/holiday/itinerary.docx``
with a file containing nothing but placeholders.
"""

import time
import zipfile

import pytest
from loguru import logger

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


def _docx_text(path) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def test_executor_shutdown_aborts_immediately(tmp_path, monkeypatch):
    """Shutdown is unrecoverable: abort, stop unstarted sections, write nothing."""
    monkeypatch.setenv("DOCX_FRAGMENT_CONCURRENCY", "2")
    llm = _RaisingLLM(RuntimeError("cannot schedule new futures after shutdown"), delay=0.05)
    out = tmp_path / "output" / "r.docx"

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
    out = tmp_path / "output" / "r.docx"

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


def test_one_failed_narration_aborts_the_report(tmp_path):
    """A report never ships a placeholder: one failed section stops the build."""
    llm = _FlakyLLM({"Budget"})
    out = tmp_path / "output" / "r.docx"

    with pytest.raises(RuntimeError, match=r"1/2 narrated sections .*Budget"):
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


def test_failed_narration_aborts_even_among_deterministic_sections(tmp_path):
    """Deterministic sections do not dilute a failed narration into an acceptable ratio."""
    llm = _RaisingLLM(ValueError("provider down"))
    out = tmp_path / "output" / "r.docx"

    with pytest.raises(RuntimeError, match="placeholder"):
        assemble_fragments(
            [
                Section("Prix", body="| A | 9.90 |"),
                Section("Stock", body="| B | 3 |"),
                Section("Intro", instruction="i", context="c"),
            ],
            _META,
            str(out),
            llm,
            system="sys",
        )

    assert not out.exists()


class _RecordingLLM:
    def __init__(self):
        self.headings: list[str] = []

    def call(self, messages):
        heading = messages[1]["content"].split("\n", 1)[0].removeprefix("Section: ")
        self.headings.append(heading)
        return f"## {heading}\n\nprose"


@pytest.fixture
def info_log():
    lines: list[str] = []
    sink_id = logger.add(lambda m: lines.append(m.record["message"]), level="INFO")
    yield lines
    logger.remove(sink_id)


@pytest.mark.parametrize("blank", ["", "   \n\t", None])
def test_narrated_section_with_blank_context_is_dropped(tmp_path, info_log, blank):
    """No context, no narration: the LLM would write the section from nothing."""
    llm = _RecordingLLM()
    out = tmp_path / "output" / "r.docx"

    assemble_fragments(
        [
            Section("Prix", body="| A | 9.90 |"),
            Section("Miracles", instruction="Raconte.", context=blank),
            Section("Intro", instruction="i", context="c"),
        ],
        _META,
        str(out),
        llm,
        system="sys",
    )

    assert llm.headings == ["Intro"]
    text = _docx_text(out)
    assert "Miracles" not in text
    assert "Prix" in text
    assert "9.90" in text
    assert "Intro" in text
    assert any("Miracles" in line and "dropped" in line for line in info_log)


def test_deterministic_section_with_empty_context_is_kept(tmp_path):
    """Only narrated sections depend on context; a verbatim body is unchanged."""
    llm = _RecordingLLM()
    out = tmp_path / "output" / "r.docx"

    assemble_fragments([Section("Prix", body="| A | 9.90 |", context="")], _META, str(out), llm, system="sys")

    assert llm.headings == []
    assert "9.90" in _docx_text(out)


def test_every_section_dropped_aborts(tmp_path):
    """A report with no section left is not a report."""
    llm = _RecordingLLM()
    out = tmp_path / "output" / "r.docx"

    with pytest.raises(ValueError, match="no section"):
        assemble_fragments(
            [
                Section("Biographie", instruction="i", context=""),
                Section("Miracles", instruction="i", context="  "),
            ],
            _META,
            str(out),
            llm,
            system="sys",
        )

    assert llm.headings == []
    assert not out.exists()
