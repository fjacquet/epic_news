import zipfile

from epic_news.models.crews.pestel_report import PestelDimension, PestelReport
from epic_news.utils.docx_report.crews.pestel import assemble_pestel_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def _dim():
    return PestelDimension(summary="s", key_factors=["kf"], impact_analysis="ia", sources=[])


def test_pestel_docx(tmp_path):
    model = PestelReport(
        topic="T",
        executive_summary="ES",
        political=_dim(),
        economic=_dim(),
        social=_dim(),
        technological=_dim(),
        environmental=_dim(),
        legal=_dim(),
        synthesis="Synth",
        generated_at="2026-07-13",
    )
    llm = _StubLLM()
    out = assemble_pestel_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    # all sections are narrated: Résumé exécutif + 6 dimensions + Synthèse = 8 llm calls
    assert llm.calls == 8
    headings = [
        "Résumé exécutif",
        "Politique",
        "Économique",
        "Social",
        "Technologique",
        "Environnemental",
        "Légal",
        "Synthèse",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
