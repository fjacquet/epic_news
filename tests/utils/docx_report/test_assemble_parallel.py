import threading
import time

from epic_news.utils.docx_report import assemble as assemble_mod
from epic_news.utils.docx_report.sections import Section


class _SlowLLM:
    def __init__(self):
        self.lock = threading.Lock()
        self.now = 0
        self.peak = 0

    def call(self, messages):
        with self.lock:
            self.now += 1
            self.peak = max(self.peak, self.now)
        time.sleep(0.03)
        with self.lock:
            self.now -= 1
        heading = messages[1]["content"].split("\n", 1)[0]
        return f"Body for {heading}"


def test_sections_narrated_in_parallel_and_in_order(monkeypatch, tmp_path):
    monkeypatch.setenv("DOCX_FRAGMENT_CONCURRENCY", "3")
    captured = {}
    monkeypatch.setattr(
        assemble_mod, "build_docx", lambda fragments, meta, path: captured.setdefault("f", fragments) and path
    )
    llm = _SlowLLM()
    sections = [Section(f"S{i}", instruction="write", context="ctx") for i in range(6)]
    sections.insert(2, Section("Fixed", body="verbatim"))

    assemble_mod.assemble_fragments(sections, {"title": "T"}, str(tmp_path / "x.docx"), llm, "sys")

    assert [h for h, _ in captured["f"]] == [s.heading for s in sections]
    assert dict(captured["f"])["Fixed"] == "verbatim"
    assert dict(captured["f"])["S4"] == "Body for Section: S4"
    assert llm.peak == 3
