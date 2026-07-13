import zipfile

from epic_news.utils.docx_report import Section, assemble_fragments


class _StubLLM:
    def __init__(self):
        self.calls = []

    def call(self, messages):
        self.calls.append(messages)
        return f"## Narrated\n\nprose for {messages[1]['content'][:20]}"


def _docx_text(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def test_deterministic_section_makes_no_llm_call(tmp_path):
    llm = _StubLLM()
    out = assemble_fragments(
        [Section("Prix", body="| Item | CHF |\n|---|---|\n| A | 9.90 |")],
        {"title": "T", "author": "Epic News", "date": "2026-07-13"},
        str(tmp_path / "r.docx"),
        llm,
        system="sys",
    )
    assert out.endswith("r.docx")
    assert llm.calls == []  # deterministic → no narration
    assert "9.90" in _docx_text(out)  # exact value preserved


def test_narrated_section_calls_llm(tmp_path):
    llm = _StubLLM()
    assemble_fragments(
        [Section("Intro", instruction="Présente.", context="ctx")],
        {"title": "T", "author": "Epic News", "date": ""},
        str(tmp_path / "n.docx"),
        llm,
        system="sys",
    )
    assert len(llm.calls) == 1
