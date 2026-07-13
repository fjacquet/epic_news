import json
import zipfile

from epic_news.utils.docx_report.crews.osint import _to_bullets, assemble_osint_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def _write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_osint_docx(tmp_path):
    _write(
        tmp_path / "global_report.json",
        {
            "target": "Cible-ACME",
            "executive_summary": "ES",
            "detailed_findings": {"supply_chain": {"risk": "Risque-Eleve"}, "gaps": ["a"]},
            "confidence_assessment": "CA",
            "information_gaps": ["Lacune-Une", "Lacune-Deux"],
        },
    )
    _write(tmp_path / "company_profile.json", {"name": "ACME-SA", "employees": 4200})
    _write(tmp_path / "tech_stack.json", {"frameworks": ["Django-Framework", "React"]})
    # Deliberately DO NOT write web_presence / hr_intelligence / legal_analysis / geospatial_analysis
    # to prove missing-file guarding.

    llm = _StubLLM()
    out = assemble_osint_docx(
        {"company": "ACME", "current_date": "2026-07-13"},
        str(tmp_path / "report.docx"),
        llm,
        osint_dir=str(tmp_path),
    )
    # Pandoc's `smart` extension curls apostrophes (' -> '); normalize so the
    # French headings can be matched with plain straight-quote literals.
    txt = _text(out).replace("’", "'")

    # nested detailed_findings rendered verbatim
    assert "Risque-Eleve" in txt
    # company_profile sub-report rendered verbatim (string + int)
    assert "ACME-SA" in txt
    assert "4200" in txt
    # tech_stack list item rendered verbatim
    assert "Django-Framework" in txt
    # information_gaps bullet rendered verbatim
    assert "Lacune-Une" in txt
    # meta title = cross-reference target
    assert "Cible-ACME" in txt

    # the four missing sub-reports must be absent
    assert "Présence web" not in txt
    assert "Renseignement RH" not in txt
    assert "Analyse juridique" not in txt
    assert "Analyse géospatiale" not in txt

    # only the two narrated sections call the LLM
    assert llm.calls == 2

    # heading order for the present sections (forward scan)
    headings = [
        "Résumé exécutif",
        "Constats détaillés",
        "Profil de l'entreprise",
        "Pile technologique",
        "Évaluation de la confiance",
        "Lacunes d'information",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)


def test_to_bullets_nested_and_empty():
    out = _to_bullets({"a": {"b": "c"}})
    assert "c" in out
    assert "**b**" in out
    # totality: empty containers never crash
    assert _to_bullets({}) == "_Aucune donnée._"
    assert _to_bullets([]) == "_Aucune donnée._"
