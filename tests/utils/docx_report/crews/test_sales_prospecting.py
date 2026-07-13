import zipfile

from epic_news.models.crews.sales_prospecting_report import KeyContact, SalesProspectingReport
from epic_news.utils.docx_report.crews.sales_prospecting import assemble_sales_prospecting_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_sales_prospecting_docx(tmp_path):
    model = SalesProspectingReport(
        company_overview="ACME est un leader du secteur.",
        key_contacts=[
            KeyContact(name="Alice-Martin", role="CTO", department="Ingénierie", contact_info="alice@ex.com"),
            KeyContact(
                name="Bob-Durand", role="VP Ventes", department="Commercial", contact_info="bob@ex.com"
            ),
        ],
        approach_strategy="Approcher via le CTO en premier.",
        remaining_information="Aucune information supplémentaire notable.",
    )
    llm = _StubLLM()
    out = assemble_sales_prospecting_docx(
        model, {"company": "ACME", "current_date": "2026-07-13"}, str(tmp_path / "sales.docx"), llm
    )
    txt = _text(out)

    for value in ["Alice-Martin", "CTO", "Bob-Durand", "alice@ex.com", "ACME"]:
        assert value in txt, f"missing verbatim value: {value}"

    # only the 3 narrated sections call the LLM; the contacts table is deterministic
    assert llm.calls == 3

    # Pandoc applies smart typography when converting Markdown to DOCX, turning the
    # straight apostrophes in our section headings into curly ones (’) in the XML.
    headings = [
        "Aperçu de l’entreprise",
        "Contacts clés",
        "Stratégie d’approche",
        "Informations complémentaires",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
