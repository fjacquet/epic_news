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
    """Create mock state JSON for testing."""
    return json.dumps({
        "crew_results": {
            "findaily": {
                "summary": "Analyse financière du jour",
                "stock_analysis": [
                    {"symbol": "AAPL", "price": 150.0, "change": 2.5}
                ],
                "crypto_analysis": [
                    {"symbol": "BTC", "price": 45000.0, "change": -1.2}
                ]
            },
            "news_daily": {
                "summary": "Actualités du jour",
                "articles": [
                    {"title": "Actualité locale", "source": "RTS", "content": "Contenu..."}
                ]
            },
            "cooking": {
                "recipe": {
                    "title": "Recette du jour",
                    "ingredients": ["Ingrédient 1", "Ingrédient 2"],
                    "instructions": ["Étape 1", "Étape 2"]
                }
            }
        },
        "report_type": "daily"
    })


class TestSelectTemplateForReport:
    """Test suite for select_template_for_report function."""

    def test_select_template_for_report_with_data(self, mock_state_json):
        """Test template selection with state data."""
        state_data = json.loads(mock_state_json)
        template_path = select_template_for_report(state_data)
        assert template_path is not None
        assert isinstance(template_path, str)
        assert "universal_report_template.html" in template_path

    def test_select_template_for_report_empty(self):
        """Test template selection with empty data."""
        empty_data = {}
        template_path = select_template_for_report(empty_data)
        assert template_path is not None
        assert isinstance(template_path, str)
        assert "universal_report_template.html" in template_path


class TestAnalyzeStateData:
    """Test suite for analyze_state_data function."""

    def test_analyze_state_data_complete(self, mock_state_data):
        """Test state data analysis with complete data."""
        analysis = analyze_state_data(mock_state_data)

        assert analysis is not None
        assert isinstance(analysis, dict)
        assert "sections" in analysis
        assert "summary" in analysis
        assert "metadata" in analysis

        # Verify sections are identified
        sections = analysis["sections"]
        assert "finance" in sections
        assert "news" in sections
        assert "cooking" in sections
        assert "saint" in sections

        # Verify section content
        assert sections["finance"]["summary"] == "Analyse financière du jour"
        assert len(sections["finance"]["stock_analysis"]) == 1
        assert sections["finance"]["stock_analysis"][0]["symbol"] == "AAPL"

    def test_analyze_state_data_empty(self):
        """Test state data analysis with empty data."""
        empty_data = {}
        analysis = analyze_state_data(empty_data)

        assert analysis is not None
        assert isinstance(analysis, dict)
        assert "sections" in analysis
        assert "summary" in analysis
        assert "metadata" in analysis
        assert len(analysis["sections"]) == 0

    def test_analyze_state_data_partial(self):
        """Test state data analysis with partial data."""
        partial_data = {
            "finance": {
                "summary": "Analyse partielle"
            }
        }
        analysis = analyze_state_data(partial_data)

        assert analysis is not None
        assert isinstance(analysis, dict)
        assert "sections" in analysis
        assert len(analysis["sections"]) == 1
        assert "finance" in analysis["sections"]

    def test_analyze_state_data_invalid_json_string(self):
        """Test state data analysis with invalid JSON string."""
        invalid_json = "invalid json string"

        with pytest.raises(Exception):
            analyze_state_data(invalid_json)

    def test_analyze_state_data_none(self):
        """Test state data analysis with None input."""
        with pytest.raises(Exception):
            analyze_state_data(None)


class TestRenderProfessionalReport:
    """Test suite for render_professional_report function."""

    def test_render_professional_report_success(self, mock_state_data):
        """Test successful professional report rendering."""
        template_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <div class="content">{{ content | safe }}</div>
            {% if sections.finance %}
            <section class="finance">
                <h2>Finance</h2>
                <p>{{ sections.finance.summary }}</p>
            </section>
            {% endif %}
        </body>
        </html>
        """

        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template') as mock_select:
                mock_select.return_value = "/mock/template/path.html"

                html_content = render_professional_report(mock_state_data, "daily")

                assert html_content is not None
                assert isinstance(html_content, str)
                assert "<!DOCTYPE html>" in html_content
                assert "lang=\"fr\"" in html_content
                assert "UTF-8" in html_content
                assert "Finance" in html_content

    def test_render_professional_report_with_analysis(self, mock_state_data):
        """Test professional report rendering with data analysis."""
        template_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Rapport Professionnel</title>
        </head>
        <body>
            <h1>Rapport du {{ date }}</h1>
            {% for section_name, section_data in sections.items() %}
            <section class="{{ section_name }}">
                <h2>{{ section_name | title }}</h2>
                {% if section_data.summary %}
                <p>{{ section_data.summary }}</p>
                {% endif %}
            </section>
            {% endfor %}
        </body>
        </html>
        """

        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template') as mock_select:
                mock_select.return_value = "/mock/template/path.html"

                html_content = render_professional_report(mock_state_data, "daily")

                assert html_content is not None
                assert "Analyse financière du jour" in html_content
                assert "Actualités du jour" in html_content

    def test_render_professional_report_template_not_found(self, mock_state_data):
        """Test professional report rendering when template file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('epic_news.utils.html_designer_utils.select_template') as mock_select:
                mock_select.return_value = "/nonexistent/template.html"

                with pytest.raises(FileNotFoundError):
                    render_professional_report(mock_state_data, "daily")

    def test_render_professional_report_invalid_template(self, mock_state_data):
        """Test professional report rendering with invalid template syntax."""
        invalid_template = """
        <!DOCTYPE html>
        <html>
        <body>
            {{ invalid_syntax_here
        </body>
        </html>
        """

        with patch('builtins.open', mock_open(read_data=invalid_template)):
            with patch('epic_news.utils.html_designer_utils.select_template') as mock_select:
                mock_select.return_value = "/mock/template/path.html"

                with pytest.raises(Exception):
                    render_professional_report(mock_state_data, "daily")

    def test_render_professional_report_empty_data(self):
        """Test professional report rendering with empty data."""
        empty_data = {}
        template_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Rapport Vide</title>
        </head>
        <body>
            <h1>Aucune donnée disponible</h1>
        </body>
        </html>
        """

        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template') as mock_select:
                mock_select.return_value = "/mock/template/path.html"

                html_content = render_professional_report(empty_data, "daily")

                assert html_content is not None
                assert "<!DOCTYPE html>" in html_content
                assert "Aucune donnée disponible" in html_content

    def test_render_professional_report_none_data(self):
        """Test professional report rendering with None data."""
        with pytest.raises(Exception):
            render_professional_report(None, "daily")


class TestHtmlDesignerUtilsIntegration:
    """Integration tests for HTML designer utilities."""

    def test_full_workflow(self, mock_state_data):
        """Test the complete workflow from data analysis to HTML generation."""
        # Step 1: Analyze data
        analysis = analyze_state_data(mock_state_data)
        assert analysis is not None

        # Step 2: Select template
        template_path = select_template("daily")
        assert template_path is not None

        # Step 3: Render report
        template_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Rapport Intégré</title>
        </head>
        <body>
            <h1>Rapport du jour</h1>
            {% for section_name, section_data in sections.items() %}
            <section>
                <h2>{{ section_name | title }}</h2>
            </section>
            {% endfor %}
        </body>
        </html>
        """

        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('epic_news.utils.html_designer_utils.select_template') as mock_select:
                mock_select.return_value = template_path

                html_content = render_professional_report(mock_state_data, "daily")

                assert html_content is not None
                assert "<!DOCTYPE html>" in html_content
                assert "lang=\"fr\"" in html_content
                assert "Rapport du jour" in html_content

    def test_error_handling_chain(self):
        """Test error handling across the utility chain."""
        # Test with invalid data that should fail gracefully
        with pytest.raises(Exception):
            analyze_state_data("invalid")

        # Test template selection with edge cases
        template_path = select_template("")
        assert template_path is not None

        # Test rendering with missing template
        with patch('builtins.open', side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                render_professional_report({}, "daily")


if __name__ == "__main__":
    pytest.main([__file__])
