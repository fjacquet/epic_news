"""
Tests unitaires simples pour les fonctions utilitaires de HtmlDesignerCrew.
"""

import json
from unittest.mock import mock_open, patch

import pytest

from epic_news.utils.html_designer_utils import (
    analyze_state_data,
    render_professional_report,
    select_template_for_report,
)


@pytest.fixture
def mock_state_json():
    """Fixture fournissant un JSON d'état simulé."""
    return json.dumps({
        "report_type": "daily",
        "finance": {
            "summary": "Analyse financière complète",
            "stocks": ["AAPL", "GOOGL", "MSFT"],
            "trends": ["Hausse des tech", "Volatilité crypto"]
        },
        "news": {
            "headlines": ["Actualité 1", "Actualité 2"],
            "sources": ["Reuters", "Bloomberg"]
        },
        "timestamp": "2024-01-15T10:00:00Z"
    })


class TestAnalyzeStateData:
    """Test suite pour la fonction analyze_state_data."""

    def test_analyze_state_data_valid_json(self, mock_state_json):
        """Test d'analyse avec un JSON valide."""
        result = analyze_state_data(mock_state_json)

        assert isinstance(result, dict)
        assert "report_type" in result
        assert "sections" in result
        assert result["report_type"] == "daily"

    def test_analyze_state_data_invalid_json(self):
        """Test d'analyse avec un JSON invalide."""
        invalid_json = "invalid json string"
        result = analyze_state_data(invalid_json)

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Invalid JSON data"

    def test_analyze_state_data_empty_string(self):
        """Test d'analyse avec une chaîne vide."""
        result = analyze_state_data("")

        assert isinstance(result, dict)
        assert "error" in result


class TestSelectTemplateForReport:
    """Test suite pour la fonction select_template_for_report."""

    def test_select_template_for_report_with_data(self):
        """Test de sélection de template avec des données."""
        state_data = {"report_type": "daily", "content": "test"}
        template_path = select_template_for_report(state_data)

        assert template_path is not None
        assert isinstance(template_path, str)
        assert "universal_report_template.html" in template_path

    def test_select_template_for_report_empty_data(self):
        """Test de sélection de template avec des données vides."""
        empty_data = {}
        template_path = select_template_for_report(empty_data)

        assert template_path is not None
        assert isinstance(template_path, str)


class TestRenderProfessionalReport:
    """Test suite pour la fonction render_professional_report."""

    def test_render_professional_report_basic(self, mock_state_json):
        """Test de rendu de rapport basique."""
        template_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Rapport Test</title>
        </head>
        <body>
            <h1>Rapport Professionnel</h1>
            <p>Contenu du rapport</p>
        </body>
        </html>
        """

        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template_for_report') as mock_select:
                mock_select.return_value = "/fake/template/path.html"

                result = render_professional_report(mock_state_json, "daily")

                assert isinstance(result, str)
                assert "<!DOCTYPE html>" in result
                assert "Rapport" in result

    def test_render_professional_report_empty_json(self):
        """Test de rendu avec JSON vide."""
        empty_json = "{}"
        template_content = "<html><body><h1>Rapport Vide</h1></body></html>"

        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template_for_report') as mock_select:
                mock_select.return_value = "/fake/template/path.html"

                result = render_professional_report(empty_json, "daily")

                assert isinstance(result, str)
                assert "<html>" in result


class TestIntegration:
    """Tests d'intégration des fonctions utilitaires."""

    def test_workflow_integration(self, mock_state_json):
        """Test du workflow complet d'analyse et de rendu."""
        # 1. Analyser les données d'état
        analysis = analyze_state_data(mock_state_json)
        assert isinstance(analysis, dict)
        assert "report_type" in analysis

        # 2. Sélectionner un template
        template_path = select_template_for_report(analysis)
        assert isinstance(template_path, str)

        # 3. Rendre le rapport (avec mock du template)
        template_content = "<html><body><h1>Test Report</h1></body></html>"
        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template_for_report') as mock_select:
                mock_select.return_value = template_path

                report = render_professional_report(mock_state_json, "daily")
                assert isinstance(report, str)
                assert "<html>" in report
