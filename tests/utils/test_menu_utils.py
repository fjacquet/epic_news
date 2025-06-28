"""Tests for the menu_utils module using pytest."""

import json
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from epic_news.utils.menu_utils import (
    embed_css_in_html,
    enhance_menu_structure,
    extract_html_from_json,
    process_recipes_from_menu,
)


@pytest.fixture
def sample_json_file():
    """Create a temporary JSON file with sample menu data."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        data = {
            "html_content": "<html><head></head><body><h1>Weekly Menu</h1></body></html>",
            "menu_items": [{"name": "Pasta", "day": "Monday"}],
        }
        tmp.write(json.dumps(data).encode("utf-8"))
        tmp_name = tmp.name

    yield tmp_name

    # Cleanup
    if os.path.exists(tmp_name):
        os.unlink(tmp_name)


def test_extract_html_from_json_success(sample_json_file):
    """Test extract_html_from_json with valid JSON file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_out:
        output_path = tmp_out.name

    with patch("epic_news.utils.menu_utils.embed_css_in_html") as mock_embed:
        with patch("epic_news.utils.menu_utils.enhance_menu_structure") as mock_enhance:
            # Set up the mocks
            mock_embed.return_value = "<html><style>body{color:black;}</style><body>Content</body></html>"
            mock_enhance.return_value = (
                "<html><style>body{color:black;}</style><body>Enhanced Content</body></html>"
            )

            result = extract_html_from_json(sample_json_file, output_path)

            assert result is True
            assert os.path.exists(output_path)
            mock_embed.assert_called_once()
            mock_enhance.assert_called_once()

    # Cleanup
    if os.path.exists(output_path):
        os.unlink(output_path)


def test_extract_html_from_json_missing_file():
    """Test extract_html_from_json with non-existent JSON file."""
    result = extract_html_from_json("/does/not/exist.json", "output.html")
    assert result is False


def test_extract_html_from_json_exception():
    """Test extract_html_from_json handles exceptions properly."""
    with patch("builtins.open", side_effect=Exception("Test exception")):
        result = extract_html_from_json("dummy.json", "output.html")
        assert result is False


def test_embed_css_in_html():
    """Test embed_css_in_html adds CSS styles."""
    html_content = '<html><head><link rel="stylesheet" href="css/menu_report.css"></head><body>Test content</body></html>'

    # Mock the file operations
    with patch("os.path.exists", return_value=True):  # noqa: SIM117
        with patch("builtins.open", mock_open(read_data="body { font-family: Arial; }")) as m:
            result = embed_css_in_html(html_content)

    # Check if CSS is embedded
    assert "<style>" in result
    assert "body { font-family: Arial; }" in result
    assert "body" in result  # Should contain some CSS rules
    assert "Test content" in result  # Original content is preserved


def test_enhance_menu_structure():
    """Test enhance_menu_structure improves menu formatting."""
    html_content = "<html><body><h1>Menu</h1><p>Day 1</p></body></html>"
    result = enhance_menu_structure(html_content)

    # The enhanced content should still contain the original content
    assert "Menu" in result
    assert "Day 1" in result
    # Should have added some enhancement (exact implementation varies)
    assert len(result) >= len(html_content)


def test_process_recipes_from_menu():
    """Test process_recipes_from_menu with mock cooking crew."""
    recipe_specs = [
        {"name": "Pasta Carbonara", "ingredients": ["pasta", "eggs"]},
        {"name": "Salad", "ingredients": ["lettuce", "tomato"]},
    ]

    mock_cooking_crew = MagicMock()
    # Mock the kickoff method to return a sample HTML content
    mock_cooking_crew.kickoff.return_value = "<html>Recipe content</html>"

    with patch("epic_news.utils.menu_utils.create_topic_slug") as mock_slug:
        # Set up the mock to return predictable slugs
        mock_slug.side_effect = ["pasta-carbonara", "salad"]

        result = process_recipes_from_menu(recipe_specs, mock_cooking_crew)

        # Should return slugs for successfully processed recipes
        assert len(result) == 2
        assert "pasta-carbonara" in result
        assert "salad" in result

        # Should have called kickoff on the cooking crew for each recipe
        assert mock_cooking_crew.kickoff.call_count == 2


def test_process_recipes_from_menu_creates_crew_if_none():
    """Test process_recipes_from_menu creates a cooking crew if none provided."""
    recipe_specs = [{"name": "Simple Recipe"}]

    with patch("epic_news.utils.menu_utils.CookingCrew") as MockCookingCrew:
        # Set up nested mocks for the CookingCrew instance
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "<html>Recipe</html>"
        MockCookingCrew.return_value.crew.return_value = mock_crew

        with patch("epic_news.utils.menu_utils.create_topic_slug", return_value="simple-recipe"):
            result = process_recipes_from_menu(recipe_specs)

            # A new cooking crew should have been created
            MockCookingCrew.assert_called_once()
            # And used to process the recipe
            mock_crew.kickoff.assert_called_once()
            assert "simple-recipe" in result


def test_process_recipes_from_menu_handles_errors():
    """Test process_recipes_from_menu handles errors during recipe processing."""
    recipe_specs = [{"name": "Error Recipe"}]

    mock_cooking_crew = MagicMock()
    # Simulate an error during processing
    mock_cooking_crew.kickoff.side_effect = Exception("Processing error")

    with patch("epic_news.utils.menu_utils.create_topic_slug", return_value="error-recipe"):  # noqa: SIM117
        with patch("epic_news.utils.menu_utils.logger") as mock_logger:
            result = process_recipes_from_menu(recipe_specs, mock_cooking_crew)

            # Should log the error
            mock_logger.error.assert_called()
            # Should not include failed recipes in results
            assert len(result) == 0
