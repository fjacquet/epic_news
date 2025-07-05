"""Tests for the menu_utils module using pytest."""


from unittest.mock import MagicMock, mock_open
from faker import Faker
from epic_news.utils.menu_utils import extract_html_from_json, embed_css_in_html, enhance_menu_structure, process_recipes_from_menu

fake = Faker()

def test_extract_html_from_json(tmp_path):
    # Test that extract_html_from_json extracts HTML content from a JSON file
    json_file = tmp_path / "test.json"
    html_file = tmp_path / "test.html"
    with open(json_file, "w") as f:
        f.write('{"html_content": "<h1>Test</h1>"}')
    assert extract_html_from_json(json_file, html_file)
    with open(html_file, "r") as f:
        assert "<h1>Test</h1>" in f.read()

def test_embed_css_in_html(mocker):
    # Test that embed_css_in_html embeds CSS content into an HTML string
    mocker.patch("builtins.open", mock_open(read_data="body {color: red;}"))
    mocker.patch("os.path.exists", return_value=True)
    html_content = '<link rel="stylesheet" href="css/menu_report.css">'
    new_html_content = embed_css_in_html(html_content)
    assert "<style>" in new_html_content
    assert "body {color: red;}" in new_html_content

def test_enhance_menu_structure():
    # Test that enhance_menu_structure enhances the menu structure with improved formatting
    html_content = "<h3>Lundi:</h3>"
    new_html_content = enhance_menu_structure(html_content)
    assert 'class="day-heading"' in new_html_content

def test_process_recipes_from_menu(mocker):
    # Test that process_recipes_from_menu processes a list of recipe specifications
    recipe_specs = [{"name": fake.sentence(), "code": "test_code"}]
    mock_cooking_crew = mocker.patch('epic_news.utils.menu_utils.CookingCrew')
    mock_crew_instance = MagicMock()
    mock_cooking_crew.return_value.crew.return_value = mock_crew_instance
    result = process_recipes_from_menu(recipe_specs, cooking_crew=mock_crew_instance)
    assert len(result) == 1
    mock_crew_instance.kickoff.assert_called_once()

