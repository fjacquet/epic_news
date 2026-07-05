"""Tests for the Cooking renderer (crew_identifier="COOKING").

Exercises CookingRenderer.render() via the public TemplateManager.render_report()
path, matching the style used in tests/utils/html/test_daily_news_html.py.
"""

from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.cooking_renderer import CookingRenderer


def _render(data: dict) -> str:
    return TemplateManager().render_report("COOKING", data)


# NOTE (pre-existing renderer bug, not fixed here): every soup.new_tag(...) call in
# CookingRenderer *except* the root container (built via create_soup, which strips the
# trailing underscore) passes `class_="..."` directly to BeautifulSoup's new_tag(). BS4
# does not special-case that kwarg, so the emitted markup literally contains a
# `class_="..."` attribute instead of `class="..."` (violates the project's own
# BaseRenderer convention documented in src/epic_news/utils/CLAUDE.md: use
# `tag.attrs["class"] = [...]`, not `class_="..."`). These CSS classes are therefore
# never applied by a browser. Tests below assert on the *actual* `class_="..."` output.


def test_full_recipe_renders_all_sections():
    """Full recipe data should render every section with the exact content fed in."""
    data = {
        "recipe_title": "Tarte Tatin Maison",
        "description": "Une tarte tatin caramelisee et fondante.",
        "type": "Dessert",
        "prep_time": "20 minutes",
        "cook_time": "45 minutes",
        "servings": 6,
        "difficulty": "facile",
        "category": "Patisserie",
        "ingredients": [
            "6 pommes Golden",
            "150 g de sucre",
            "1 pate feuilletee",
        ],
        "instructions": [
            "Eplucher et couper les pommes.",
            "Faire un caramel avec le sucre.",
            "Cuire au four 45 minutes.",
        ],
        "chef_notes": ["Utiliser un moule qui va au four", "Laisser tiedir avant de demouler"],
        "nutritional_info": {"calories": "320 kcal", "sucres": "28 g"},
    }

    html = _render(data)

    # Overall document structure produced by the universal template.
    assert "<!DOCTYPE html>" in html
    # Renderer's own container marker.
    assert 'class="recipe-container"' in html

    # Header content
    assert "🍽️ Tarte Tatin Maison" in html
    assert "Une tarte tatin caramelisee et fondante." in html
    assert "Dessert" in html

    # Metadata
    assert "20 minutes" in html
    assert "45 minutes" in html
    assert "6" in html
    assert "🟢 Facile" in html  # difficulty mapped from "facile"
    assert "Patisserie" in html

    # Ingredients section + exact items
    # NOTE: renderer emits a literal `class_="..."` attribute here (see bug note above).
    assert 'class_="recipe-ingredients"' in html
    assert "🧂 Ingrédients" in html
    assert "🥄 6 pommes Golden" in html
    assert "🥄 150 g de sucre" in html
    assert "🥄 1 pate feuilletee" in html

    # Instructions section + exact steps
    assert 'class_="recipe-instructions"' in html
    assert "📝 Instructions" in html
    assert "Eplucher et couper les pommes." in html
    assert "Faire un caramel avec le sucre." in html
    assert "Cuire au four 45 minutes." in html

    # Chef notes (list branch)
    assert 'class_="chef-notes"' in html
    assert "Utiliser un moule qui va au four" in html
    assert "Laisser tiedir avant de demouler" in html

    # Nutritional info (dict branch) - keys are humanized via replace('_',' ').title()
    assert 'class_="nutritional-info"' in html
    assert "320 kcal" in html
    assert "28 g" in html


def test_minimal_data_renders_without_crash():
    """Empty data must not crash and should fall back to defaults, skipping optional sections."""
    html = _render({})

    assert "<!DOCTYPE html>" in html
    assert 'class="recipe-container"' in html
    # Fallback title
    assert "🍽️ Recette" in html

    # No optional sections should appear at all.
    assert 'class_="recipe-ingredients"' not in html
    assert 'class_="recipe-instructions"' not in html
    assert 'class_="chef-notes"' not in html
    assert 'class_="nutritional-info"' not in html
    # Metadata div only appended when it has content - with no fields at all it's skipped.
    assert 'class_="recipe-meta"' not in html

    # Still a non-trivial, well-formed HTML document.
    assert len(html) > 200


def test_name_fallback_used_when_no_recipe_title():
    """`name` key should be used as title fallback when `recipe_title` is absent."""
    html = _render({"name": "Soupe de Legumes"})

    assert "🍽️ Soupe de Legumes" in html


def test_badge_uses_category_when_type_missing():
    """Badge and metadata both read `category` when `type` is absent."""
    html = _render({"recipe_title": "Ratatouille", "category": "Plat Principal"})

    assert "Plat Principal" in html
    assert 'class_="recipe-meta"' in html
    assert "🏷️ Catégorie:" in html


def test_difficulty_unrecognized_value_falls_back_to_raw_text():
    """An unmapped difficulty string should be shown as-is (fallback branch of the emoji map)."""
    html = _render({"recipe_title": "Plat Mystere", "difficulty": "extreme"})

    assert "📊 Difficulté:" in html
    assert "extreme" in html
    # None of the known emoji mappings should have been substituted.
    assert "🟢 Facile" not in html
    assert "🟡 Moyen" not in html
    assert "🔴 Difficile" not in html


def test_difficulty_case_insensitive_mapping():
    """Difficulty lookup lowercases input, so mixed-case values still map to emoji labels."""
    html = _render({"recipe_title": "Plat Difficile", "difficulty": "DIFFICILE"})

    assert "🔴 Difficile" in html


def test_chef_notes_as_plain_string_renders_paragraph_not_list():
    """String chef_notes (not list) should render as a single <p>, not a <ul>."""
    renderer = CookingRenderer()
    html = renderer.render({"recipe_title": "Quiche", "chef_notes": "Servir tiede."})

    assert 'class_="chef-notes"' in html
    assert "Servir tiede." in html
    assert 'class_="notes-list"' not in html
    assert "<p>Servir tiede.</p>" in html


def test_nutritional_info_as_plain_string_renders_paragraph_not_list():
    """String nutritional_info (not dict) should render as a single <p>, not a <ul>."""
    renderer = CookingRenderer()
    html = renderer.render({"recipe_title": "Quiche", "nutritional_info": "Environ 400 kcal par part."})

    assert 'class_="nutritional-info"' in html
    assert "Environ 400 kcal par part." in html
    assert 'class_="nutrition-list"' not in html


def test_single_ingredient_and_instruction_still_render_list_structures():
    """Even a single ingredient/instruction should be wrapped in ul/ol list structures."""
    renderer = CookingRenderer()
    html = renderer.render(
        {
            "recipe_title": "Oeuf Dur",
            "ingredients": ["1 oeuf"],
            "instructions": ["Cuire 10 minutes dans l'eau bouillante."],
        }
    )

    assert 'class_="ingredients-list"' in html
    assert 'class_="instructions-list"' in html
    assert "🥄 1 oeuf" in html
    assert "Cuire 10 minutes dans l'eau bouillante." in html


def test_missing_ingredients_and_instructions_skip_their_sections():
    """When ingredients/instructions keys are absent entirely, their sections are skipped."""
    renderer = CookingRenderer()
    html = renderer.render({"recipe_title": "Recette Vide"})

    assert 'class_="recipe-ingredients"' not in html
    assert 'class_="recipe-instructions"' not in html
