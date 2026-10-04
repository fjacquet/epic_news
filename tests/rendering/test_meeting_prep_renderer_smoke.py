"""Smoke test: a sample MeetingPrepReport renders to HTML via TemplateManager."""

import json

from epic_news.models.crews.meeting_prep_report import MeetingPrepReport
from epic_news.utils.html.template_manager import TemplateManager


def generate_sample_meeting_prep_data():
    """Generate a sample MeetingPrepReport for testing."""
    sample_data = {
        "title": "Test Meeting",
        "summary": "Préparation pour la réunion stratégique avec Acme Corp pour discuter des possibilités de partenariat technologique.",
        "company_profile": {
            "name": "Acme Corporation",
            "industry": "Technologies",
            "market_position": "Leader sur le marché des solutions cloud pour entreprises",
        },
        "participants": [
            {
                "name": "Jean Dupont",
                "role": "CEO",
                "background": "Fondateur d'Acme, 15 ans d'expérience dans le secteur technologique",
            },
            {
                "name": "Marie Martin",
                "role": "CTO",
                "background": "Anciennement chez Google, experte en IA et cloud computing",
            },
        ],
        "industry_overview": "Le secteur des technologies cloud est en pleine expansion avec une croissance annuelle de 25%. Les tendances actuelles incluent l'adoption de l'IA, le edge computing et les solutions multi-cloud.",
        "talking_points": [
            {
                "topic": "Possibilités d'intégration API",
                "key_points": [
                    "Quelles sont vos API actuelles?",
                    "Comment envisagez-vous l'interopérabilité?",
                ],
                "questions": [],
            },
            {
                "topic": "Roadmap technologique",
                "key_points": [
                    "Quelles sont vos priorités pour les 12 prochains mois?",
                    "Comment voyez-vous l'évolution du marché?",
                ],
                "questions": [],
            },
        ],
        "strategic_recommendations": [
            {
                "area": "Partenariat stratégique",
                "suggestion": "Établir un partenariat technologique pour l'intégration de nos solutions respectives.",
                "expected_outcome": "Increased market share",
            },
            {
                "area": "Développement conjoint",
                "suggestion": "Envisager un développement conjoint d'une solution cloud-IA pour le secteur financier.",
                "expected_outcome": "New revenue stream",
            },
        ],
        "additional_resources": [
            {
                "title": "Rapport d'analyse Acme Corp",
                "link": "https://example.com/reports/acme",
                "description": "Analyse détaillée des produits et de la position d'Acme Corp sur le marché.",
            },
            {
                "title": "Étude de marché Cloud 2023",
                "link": "https://example.com/market/cloud2023",
                "description": "Tendances et prévisions pour le marché du cloud computing.",
            },
        ],
    }

    # Create a Pydantic model from the data
    return MeetingPrepReport.model_validate(sample_data)


def test_meeting_prep_renderer(tmp_path):
    """Render a sample report with MeetingPrepRenderer and write it under tmp_path."""
    meeting_prep_report = generate_sample_meeting_prep_data()

    json_path = tmp_path / "sample_meeting_prep.json"
    json_path.write_text(
        json.dumps(meeting_prep_report.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    html = TemplateManager().render_report("MEETING_PREP", meeting_prep_report)
    html_path = tmp_path / "meeting_preparation_test.html"
    html_path.write_text(html, encoding="utf-8")

    assert html_path.read_text(encoding="utf-8") == html
    assert "Acme Corporation" in html
    assert "Jean Dupont" in html
