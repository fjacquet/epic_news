"""Tests for the Menu HTML renderer (MenuRenderer), exercised via the public
``TemplateManager.render_report("MENU", data)`` path (see ``renderer_factory.py``
for the ``"MENU" -> MenuRenderer`` mapping).

``MenuRenderer`` reads keys the current ``WeeklyMenuPlan`` Pydantic model does not
directly produce (e.g. ``daily_plans`` vs. the model's ``daily_menus``), so these
tests build plain dicts matching what the renderer actually reads, reusing the
``DailyMeal``/``DishInfo`` sub-models where their shape lines up with a real
renderer branch (the "old format" starter/main_course/dessert meal).
"""

import pytest

from epic_news.models.crews.menu_designer_report import DailyMeal, DishInfo, DishType, MealType
from epic_news.utils.html.template_manager import TemplateManager


@pytest.fixture
def full_menu_data() -> dict:
    """A realistic, fully populated MENU data dict exercising every renderer branch."""
    lundi_lunch_old_format = DailyMeal(
        meal_type=MealType.DEJEUNER,
        starter=DishInfo(
            name="Salade de saison",
            dish_type=DishType.ENTREE,
            description="Salade fraîche de légumes de saison.",
            seasonal_ingredients=["tomate", "concombre"],
            nutritional_highlights="Riche en fibres",
        ),
        main_course=DishInfo(
            name="Filet de poulet aux herbes",
            dish_type=DishType.PLAT_PRINCIPAL,
            description="Poulet grillé aux herbes de Provence.",
            seasonal_ingredients=["poulet", "thym"],
            nutritional_highlights="Riche en protéines",
        ),
        dessert=None,
    ).model_dump()

    lundi_dinner_new_format = {
        "dishes": [
            {"name": "Velouté de courge", "dish_type": "entrée"},
            {"name": "Poulet rôti", "dish_type": "plat principal"},
            {"name": "Tarte aux pommes", "dish_type": "dessert"},
            {"name": "", "dish_type": "entrée"},  # empty name must be skipped
        ]
    }

    return {
        "title": "Menu de la Semaine Test",
        "date_range": "01-07 Juillet 2026",
        "description": "Un menu équilibré et savoureux, pensé pour toute la famille.",
        "weekly_overview": "Cette semaine met l'accent sur les produits de saison.",
        "daily_plans": [
            # 1) "day"-keyed dict branch (mirrors DailyMenu shape): meals is
            #    hard-derived by the renderer as {"lunch": ..., "dinner": ...}
            {
                "day": "Lundi",
                "date": "2026-07-06",
                "lunch": lundi_lunch_old_format,
                "dinner": lundi_dinner_new_format,
            },
            # 2) legacy [day, meals-dict] tuple branch, with breakfast/snacks as
            #    lists of dish strings, a plain-text lunch, a dict meal with no
            #    recognized keys, and an unmapped custom meal type
            [
                "Samedi",
                {
                    "breakfast": ["Croissant", "Jus d'orange"],
                    "lunch": "Barbecue en famille",
                    "dinner": ["Salade grecque", "Poisson grillé"],
                    "snacks": ["Fruits secs", "Yaourt nature"],
                    "gouter": {"note": "à voir avec les enfants"},
                },
            ],
            # 3) legacy [day, flat-list] tuple branch + unknown day name -> fallback emoji
            ["JourInconnu", ["Soupe", "Pain", "Fromage"]],
        ],
        "shopping_list": {
            "Fruits et légumes": ["Tomates", "Courgettes", "Pommes"],
            "Viandes et poissons": ["Poulet", "Saumon"],
        },
        "nutritional_info": {
            "Calories": "14000 kcal/semaine",
            "Protéines": "560g",
            "Fibres": "210g",
        },
    }


def test_menu_full_kitchen_sink_all_sections(full_menu_data):
    """Full data set: header, overview, three day formats, shopping list, nutrition table."""
    html = TemplateManager().render_report("MENU", full_menu_data)

    # Structural markers
    assert "<!DOCTYPE html>" in html
    assert 'class_="menu-header"' in html
    assert 'class_="menu-overview"' in html
    assert 'class_="daily-plans"' in html
    assert 'class_="shopping-list"' in html
    assert 'class_="nutritional-info"' in html
    assert 'class_="nutrition-table"' in html
    assert html.count('class_="day-plan"') == 3

    # Header (title + date range + description)
    assert "🍽️ Menu de la Semaine Test" in html
    assert "01-07 Juillet 2026" in html
    assert "Un menu équilibré et savoureux, pensé pour toute la famille." in html

    # Weekly overview section
    assert "Cette semaine met l'accent sur les produits de saison." in html

    # Day 1 ("day"-dict branch): day emoji, old starter/main/dessert format
    # (dessert=None skipped) + new "dishes" array format (empty name skipped)
    assert "1️⃣ Lundi" in html
    assert "🥗 Entrée: Salade de saison" in html
    assert "🍽️ Plat principal: Filet de poulet aux herbes" in html
    assert "🥗 Entrée: Velouté de courge" in html
    assert "🍽️ Plat principal: Poulet rôti" in html
    assert "🍮 Dessert: Tarte aux pommes" in html
    # Two "Entrée:" dishes total (old + new); the empty-name dish is skipped
    assert html.count("🥗 Entrée:") == 2
    # Only the new-format dessert renders; the old-format dessert=None is skipped
    assert html.count("🍮 Dessert:") == 1

    # Day 2 (legacy [day, meals] tuple branch): breakfast/snacks lists,
    # plain-text lunch, unmapped custom meal type, unrecognized dict meal_content
    assert "6️⃣ Samedi" in html
    assert "🍳 Petit-déjeuner" in html
    assert "Croissant" in html
    assert "Jus d'orange" in html
    assert "🥗 Déjeuner" in html
    assert "Barbecue en famille" in html
    assert "🍲 Dîner" in html
    assert "Salade grecque" in html
    assert "Poisson grillé" in html
    assert "🍎 Collations" in html
    assert "Fruits secs" in html
    assert "Yaourt nature" in html
    assert "🍽️ gouter" in html  # unmapped meal type falls back to raw key
    assert "{'note': 'à voir avec les enfants'}" in html  # unrecognized dict stringified

    # Day 3 (legacy [day, flat-list] tuple branch; unknown day -> generic emoji)
    assert "🗓️ JourInconnu" in html
    assert "Soupe" in html
    assert "Pain" in html
    assert "Fromage" in html

    # Shopping list (category/dict branch)
    assert "Fruits et légumes" in html
    assert "Tomates" in html
    assert "Courgettes" in html
    assert "Viandes et poissons" in html
    assert "Saumon" in html

    # Nutritional info (dict/table branch)
    assert "Calories" in html
    assert "14000 kcal/semaine" in html
    assert "Protéines" in html
    assert "560g" in html


def test_menu_minimal_data_no_crash_default_title():
    """Empty data: renderer must not crash, uses default title, skips optional sections."""
    html = TemplateManager().render_report("MENU", {})

    assert "<!DOCTYPE html>" in html
    assert "🍽️ Menu Hebdomadaire" in html  # default title fallback
    assert 'class_="menu-header"' in html

    # All optional sections/branches must be entirely absent
    assert 'class_="menu-date-range"' not in html
    assert 'class_="menu-description"' not in html
    assert 'class_="menu-overview"' not in html
    assert 'class_="daily-plans"' not in html
    assert 'class_="menu-content"' not in html
    assert 'class_="shopping-list"' not in html
    assert 'class_="nutritional-info"' not in html


def test_menu_shopping_list_simple_list_and_content_fallback():
    """Shopping list as a flat list (not dict) + empty daily_plans -> content fallback branch."""
    data = {
        "title": "Menu Express",
        "content": "Menu libre : improvisez selon vos envies cette semaine !",
        "shopping_list": ["Pain", "Lait", "Oeufs"],
    }
    html = TemplateManager().render_report("MENU", data)

    assert 'class_="menu-content"' in html
    assert "Menu libre : improvisez selon vos envies cette semaine !" in html
    # daily_plans absent -> no daily-plans section, only the content fallback div
    assert 'class_="daily-plans"' not in html

    assert 'class_="shopping-list"' in html
    assert "Pain" in html
    assert "Lait" in html
    assert "Oeufs" in html
    # Simple (non-dict) shopping list must not create category subdivisions
    assert 'class_="shopping-category"' not in html


def test_menu_nutritional_info_as_text_and_unknown_dish_type_fallback():
    """nutritional_info as plain text uses the text branch (not the table);
    an unrecognized dish_type falls back to the generic 🍽️ emoji."""
    data = {
        "title": "Menu Simple",
        "daily_plans": [
            {
                "day": "Mercredi",
                "lunch": {"dishes": [{"name": "Plat mystère", "dish_type": "surprise"}]},
                "dinner": {"dishes": []},
            }
        ],
        "nutritional_info": "Environ 2000 kcal par jour, riche en fibres et protéines.",
    }
    html = TemplateManager().render_report("MENU", data)

    assert 'class_="nutritional-info"' in html
    assert "Environ 2000 kcal par jour, riche en fibres et protéines." in html
    assert 'class_="nutrition-table"' not in html  # plain-text branch, not the table branch

    assert "3️⃣ Mercredi" in html
    # Unrecognized dish_type "surprise" falls back to the generic emoji + capitalized type
    assert "🍽️ Surprise: Plat mystère" in html
