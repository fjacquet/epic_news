import zipfile

from epic_news.models.crews.meeting_prep_report import (
    AdditionalResource,
    CompanyProfile,
    MeetingPrepReport,
    Participant,
    StrategicRecommendation,
    TalkingPoint,
)
from epic_news.utils.docx_report.crews.meeting_prep import assemble_meeting_prep_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_meeting_prep_docx(tmp_path):
    model = MeetingPrepReport(
        title="Réunion-ACME",
        summary="Contexte.",
        company_profile=CompanyProfile(
            name="ACME-SA",
            industry="Tech",
            key_products=["Widget-Pro"],
            market_position="Leader",
        ),
        participants=[Participant(name="Alice-Martin", role="CTO", background="Ex-Google")],
        industry_overview="Secteur en croissance.",
        talking_points=[
            TalkingPoint(topic="Sujet-Budget", key_points=["Point-Un"], questions=["Question-A"])
        ],
        strategic_recommendations=[
            StrategicRecommendation(
                area="Domaine-Vente", suggestion="Suggestion-X", expected_outcome="Résultat-Y"
            )
        ],
        additional_resources=[AdditionalResource(title="Ressource-Doc", description="desc", link=None)],
    )
    llm = _StubLLM()
    out = assemble_meeting_prep_docx(
        model, {"current_date": "2026-07-13"}, str(tmp_path / "meeting.docx"), llm
    )
    txt = _text(out)

    # Company profile (deterministic)
    for figure in ["ACME-SA", "Widget-Pro"]:
        assert figure in txt, f"missing verbatim figure: {figure}"

    # Participants table (deterministic)
    for figure in ["Alice-Martin", "CTO"]:
        assert figure in txt, f"missing verbatim figure: {figure}"

    # Talking points (deterministic)
    for figure in ["Sujet-Budget", "Point-Un", "Question-A"]:
        assert figure in txt, f"missing verbatim figure: {figure}"

    # Strategic recommendations (deterministic)
    for figure in ["Domaine-Vente", "Suggestion-X", "Résultat-Y"]:
        assert figure in txt, f"missing verbatim figure: {figure}"

    # Resources (deterministic), link=None must be guarded
    assert "Ressource-Doc" in txt
    assert "None" not in txt

    # Only Résumé + Aperçu du secteur are narrated
    assert llm.calls == 2

    # Heading order (curly apostrophe: Pandoc renders straight ' as curly ’)
    headings = [
        "Résumé",
        "Profil de l’entreprise",
        "Participants",
        "Aperçu du secteur",
        "Points de discussion",
        "Recommandations stratégiques",
        "Ressources",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
