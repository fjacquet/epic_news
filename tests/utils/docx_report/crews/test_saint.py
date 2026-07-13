import zipfile

from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.utils.docx_report.crews.saint import assemble_saint_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_saint_docx(tmp_path):
    model = SaintData(
        saint_name="Saint Nicolas",
        feast_date="6 décembre",
        biography="bio",
        significance="sig",
        miracles="mir",
        swiss_connection="swiss",
        prayer_reflection="prayer",
        sources=["Source-Un", "Source-Deux"],
    )
    llm = _StubLLM()
    out = assemble_saint_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    assert "Source-Un" in txt and "Source-Deux" in txt  # deterministic sources verbatim
    # narrated: Biographie + Signification + Miracles + Lien avec la Suisse + Prière & Réflexion = 5 llm calls
    # (Sources is a deterministic body -> no LLM)
    assert llm.calls == 5
    headings = [
        "Biographie",
        "Signification",
        "Miracles",
        "Lien avec la Suisse",
        "Prière &amp; Réflexion",  # XML-escapes "&" in the run text
        "Sources",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
