import zipfile

from epic_news.models.crews.financial_report import AssetAnalysis, AssetSuggestion, FinancialReport
from epic_news.utils.docx_report.crews.fin_daily import assemble_fin_daily_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_fin_daily_docx(tmp_path):
    model = FinancialReport(
        title="Rapport financier quotidien",
        executive_summary="Les marchés progressent.",
        analyses=[
            AssetAnalysis(
                asset_class="Actions",
                summary="+12.5% YTD",
                details=["P/E 18.3", "div 2.1%"],
            )
        ],
        suggestions=[
            AssetSuggestion(
                asset_class="Crypto",
                suggestion="Réduire à 4200 CHF",
                rationale="volatilité",
            )
        ],
        report_date="2026-07-13",
    )
    llm = _StubLLM()
    out = assemble_fin_daily_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "fin.docx"), llm)
    txt = _text(out)

    for figure in ["12.5", "18.3", "4200", "Réduire"]:
        assert figure in txt, f"missing verbatim figure: {figure}"

    # only the exec summary narrates; both tables are deterministic
    assert llm.calls == 1

    headings = ["Résumé exécutif", "Analyses", "Suggestions"]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
