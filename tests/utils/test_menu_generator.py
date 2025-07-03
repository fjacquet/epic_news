"""Tests for menu_generator utility."""

import json

import pytest

from epic_news.utils.menu_generator import MenuGenerator


@pytest.fixture
def sample_menu_structure():
    """Provide a sample menu structure for testing."""
    return {
        "week_start_date": "2025-06-30",
        "season": "été",
        "daily_menus": [
            {
                "day": "Lundi",
                "date": "2025-06-30",
                "lunch": {
                    "meal_type": "déjeuner",
                    "starter": {"name": "Salade de tomates", "dish_type": "entrée"},
                    "main_course": {"name": "Poulet rôti", "dish_type": "plat principal"},
                    "dessert": None,
                },
                "dinner": {
                    "meal_type": "dîner",
                    "main_course": {"name": "Soupe de légumes", "dish_type": "plat principal"},
                },
            },
            {
                "day": "Mardi",
                "date": "2025-07-01",
                "lunch": {
                    "meal_type": "déjeuner",
                    "main_course": {"name": "Poisson grillé", "dish_type": "plat principal"},
                    "dessert": {"name": "Mousse au chocolat", "dish_type": "dessert"},
                },
            },
        ],
    }


def test_calculate_season():
    """Test that the season is calculated correctly."""
    # This test is dependent on the current date, so it's not ideal.
    # A better implementation would pass the date to the function.
    # For now, we'll just test that it returns a valid season.
    assert MenuGenerator.calculate_season() in ["hiver", "printemps", "été", "automne"]


def test_parse_menu_structure_from_dict(sample_menu_structure):
    """Test parsing a menu structure from a dictionary."""
    recipes = MenuGenerator.parse_menu_structure(sample_menu_structure)
    assert len(recipes) == 4
    assert recipes[0]["name"] == "Salade de tomates"
    assert recipes[0]["type"] == "entrée"
    assert recipes[0]["code"] == "LUN-L-S01"
    assert recipes[1]["name"] == "Poulet rôti"
    assert recipes[1]["type"] == "plat principal"
    assert recipes[1]["code"] == "LUN-L-M01"
    assert recipes[2]["name"] == "Soupe de légumes"
    assert recipes[2]["type"] == "plat principal"
    assert recipes[2]["code"] == "LUN-D-M02"
    assert recipes[3]["name"] == "Poisson grillé"
    assert recipes[3]["type"] == "plat principal"
    assert recipes[3]["code"] == "MAR-L-M03"


def test_parse_menu_structure_from_json_string(sample_menu_structure):
    """Test parsing a menu structure from a JSON string."""
    json_string = json.dumps(sample_menu_structure)
    recipes = MenuGenerator.parse_menu_structure(json_string)
    assert len(recipes) == 4
    assert recipes[0]["name"] == "Salade de tomates"


def test_parse_menu_structure_empty():
    """Test parsing an empty menu structure."""
    recipes = MenuGenerator.parse_menu_structure({})
    assert len(recipes) == 0


def test_parse_menu_structure_malformed(sample_menu_structure):
    """Test parsing a malformed menu structure."""
    # Remove 'name' from one of the dishes
    del sample_menu_structure["daily_menus"][0]["lunch"]["starter"]["name"]
    recipes = MenuGenerator.parse_menu_structure(sample_menu_structure)
    assert len(recipes) == 3  # The malformed entry should be skipped


def test_parse_menu_structure_invalid_input():
    """Test parsing with an invalid input type."""
    with pytest.raises(TypeError):
        MenuGenerator.parse_menu_structure(123)
