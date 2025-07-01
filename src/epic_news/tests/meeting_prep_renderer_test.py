"""
Test script for the MeetingPrepRenderer integration.
This script creates a sample MeetingPrepReport and renders it to HTML.
"""

import os
import json
from pathlib import Path

from epic_news.models.meeting_prep_report import MeetingPrepReport, CompanyProfile, Participant
from epic_news.utils.html.meeting_prep_html_factory import meeting_prep_to_html


def generate_sample_meeting_prep_data():
    """Generate a sample MeetingPrepReport for testing."""
    sample_data = {
        "summary": "Préparation pour la réunion stratégique avec Acme Corp pour discuter des possibilités de partenariat technologique.",
        "company_profile": {
            "name": "Acme Corporation",
            "industry": "Technologies",
            "market_position": "Leader sur le marché des solutions cloud pour entreprises"
        },
        "participants": [
            {
                "name": "Jean Dupont",
                "role": "CEO",
                "background": "Fondateur d'Acme, 15 ans d'expérience dans le secteur technologique"
            },
            {
                "name": "Marie Martin",
                "role": "CTO",
                "background": "Anciennement chez Google, experte en IA et cloud computing"
            }
        ],
        "industry_overview": "Le secteur des technologies cloud est en pleine expansion avec une croissance annuelle de 25%. Les tendances actuelles incluent l'adoption de l'IA, le edge computing et les solutions multi-cloud.",
        "talking_points": [
            {
                "key_point": "Possibilités d'intégration API",
                "questions": [
                    "Quelles sont vos API actuelles?",
                    "Comment envisagez-vous l'interopérabilité?"
                ]
            },
            {
                "key_point": "Roadmap technologique",
                "questions": [
                    "Quelles sont vos priorités pour les 12 prochains mois?",
                    "Comment voyez-vous l'évolution du marché?"
                ]
            }
        ],
        "strategic_recommendations": [
            {
                "title": "Partenariat stratégique",
                "description": "Établir un partenariat technologique pour l'intégration de nos solutions respectives."
            },
            {
                "title": "Développement conjoint",
                "description": "Envisager un développement conjoint d'une solution cloud-IA pour le secteur financier."
            }
        ],
        "additional_resources": [
            {
                "title": "Rapport d'analyse Acme Corp",
                "url": "https://example.com/reports/acme",
                "description": "Analyse détaillée des produits et de la position d'Acme Corp sur le marché."
            },
            {
                "title": "Étude de marché Cloud 2023",
                "url": "https://example.com/market/cloud2023",
                "description": "Tendances et prévisions pour le marché du cloud computing."
            }
        ]
    }
    
    # Create a Pydantic model from the data
    return MeetingPrepReport.model_validate(sample_data)


def test_meeting_prep_renderer():
    """Test the MeetingPrepRenderer by generating HTML from a sample report."""
    # Create output directory if it doesn't exist
    output_dir = Path("output/meeting")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate sample data
    meeting_prep_report = generate_sample_meeting_prep_data()
    print(f"✅ Created sample MeetingPrepReport: {meeting_prep_report.company_profile.name}")
    
    # Save JSON for reference
    with open(output_dir / "sample_meeting_prep.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(meeting_prep_report.model_dump(), indent=2, ensure_ascii=False))
    print(f"✅ Saved sample JSON to {output_dir / 'sample_meeting_prep.json'}")
    
    # Generate HTML using our new renderer
    html_output_path = output_dir / "meeting_preparation_test.html"
    html = meeting_prep_to_html(meeting_prep_report, html_file=str(html_output_path))
    print(f"✅ Generated HTML using MeetingPrepRenderer")
    print(f"✅ Saved HTML to {html_output_path}")
    
    print(f"\nTest completed. Please check the HTML output at: file://{html_output_path.resolve()}")


if __name__ == "__main__":
    test_meeting_prep_renderer()
