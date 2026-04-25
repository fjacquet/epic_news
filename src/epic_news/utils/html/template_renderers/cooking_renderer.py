"""
Cooking Renderer

Renders cooking recipe data to structured HTML using BeautifulSoup.
Handles recipe details, ingredients, instructions and metadata.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class CookingRenderer(BaseRenderer):
    """Renders cooking recipe content with structured formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any]) -> str:
        """
        Render cooking recipe data to HTML.

        Args:
            data: Dictionary containing recipe data

        Returns:
            HTML string for recipe content
        """
        # Create main container
        soup = self.create_soup("div", class_="recipe-container")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add recipe metadata
        self._add_metadata(soup, container, data)

        # Add ingredients section
        self._add_ingredients(soup, container, data)

        # Add instructions section
        self._add_instructions(soup, container, data)

        # Add chef notes if available
        self._add_chef_notes(soup, container, data)

        # Add nutritional info if available
        self._add_nutritional_info(soup, container, data)


        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recipe header with title and description."""
        header = soup.new_tag("header", class_="recipe-header")

        # Title
        title = data.get("recipe_title", data.get("name", "Recette"))
        title_tag = soup.new_tag("h1", class_="recipe-title")
        title_tag.string = f"🍽️ {title}"
        header.append(title_tag)

        # Description
        description = data.get("description", "")
        if description:
            desc_tag = soup.new_tag("p", class_="recipe-description")
            desc_tag.string = description
            header.append(desc_tag)

        # Add recipe type badge if available
        recipe_type = data.get("type", data.get("category", ""))
        if recipe_type:
            badge = soup.new_tag("span", class_="recipe-badge")
            badge.string = recipe_type
            header.append(badge)

        container.append(header)

    def _add_metadata(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recipe metadata (prep time, cook time, servings, etc.)."""
        meta_div = soup.new_tag("div", class_="recipe-meta")

        # Add preparation time if available
        prep_time = data.get("prep_time", "")
        if prep_time:
            prep_div = soup.new_tag("div", class_="meta-item")
            prep_strong = soup.new_tag("strong")
            prep_strong.string = "⏱️ Préparation: "
            prep_div.append(prep_strong)
            prep_div.append(soup.new_string(prep_time))
            meta_div.append(prep_div)

        # Add cooking time if available
        cook_time = data.get("cook_time", "")
        if cook_time:
            cook_div = soup.new_tag("div", class_="meta-item")
            cook_strong = soup.new_tag("strong")
            cook_strong.string = "🔥 Cuisson: "
            cook_div.append(cook_strong)
            cook_div.append(soup.new_string(cook_time))
            meta_div.append(cook_div)

        # Add servings if available
        servings = data.get("servings", "")
        if servings:
            serv_div = soup.new_tag("div", class_="meta-item")
            serv_strong = soup.new_tag("strong")
            serv_strong.string = "👥 Portions: "
            serv_div.append(serv_strong)
            serv_div.append(soup.new_string(str(servings)))
            meta_div.append(serv_div)

        # Add difficulty if available
        difficulty = data.get("difficulty", "")
        if difficulty:
            # Map difficulty to emoji
            difficulty_emoji = {
                "facile": "🟢 Facile",
                "moyen": "🟡 Moyen",
                "difficile": "🔴 Difficile",
                "easy": "🟢 Facile",
                "medium": "🟡 Moyen",
                "hard": "🔴 Difficile",
            }.get(difficulty.lower(), difficulty)

            diff_div = soup.new_tag("div", class_="meta-item")
            diff_strong = soup.new_tag("strong")
            diff_strong.string = "📊 Difficulté: "
            diff_div.append(diff_strong)
            diff_div.append(soup.new_string(difficulty_emoji))
            meta_div.append(diff_div)

        # Add category if available
        category = data.get("category", "")
        if category:
            cat_div = soup.new_tag("div", class_="meta-item")
            cat_strong = soup.new_tag("strong")
            cat_strong.string = "🏷️ Catégorie: "
            cat_div.append(cat_strong)
            cat_div.append(soup.new_string(category))
            meta_div.append(cat_div)

        if len(meta_div.contents) > 0:
            container.append(meta_div)

    def _add_ingredients(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add ingredients section with structured list."""
        ingredients = data.get("ingredients", [])
        if not ingredients:
            return

        ingredients_section = soup.new_tag("section", class_="recipe-ingredients")

        # Add section title
        ing_title = soup.new_tag("h2")
        ing_title.string = "🧂 Ingrédients"
        ingredients_section.append(ing_title)

        # Create ingredients list
        ing_list = soup.new_tag("ul", class_="ingredients-list")
        for ingredient in ingredients:
            ing_item = soup.new_tag("li")
            ing_item.string = f"🥄 {ingredient}"
            ing_list.append(ing_item)

        ingredients_section.append(ing_list)
        container.append(ingredients_section)

    def _add_instructions(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add instructions section with numbered steps."""
        instructions = data.get("instructions", [])
        if not instructions:
            return

        instructions_section = soup.new_tag("section", class_="recipe-instructions")

        # Add section title
        ins_title = soup.new_tag("h2")
        ins_title.string = "📝 Instructions"
        instructions_section.append(ins_title)

        # Create instructions list
        ins_list = soup.new_tag("ol", class_="instructions-list")
        for instruction in instructions:
            ins_item = soup.new_tag("li")
            ins_item.string = instruction
            ins_list.append(ins_item)

        instructions_section.append(ins_list)
        container.append(instructions_section)

    def _add_chef_notes(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add chef notes if available."""
        chef_notes = data.get("chef_notes", "")
        if not chef_notes:
            return

        notes_section = soup.new_tag("section", class_="chef-notes")

        notes_title = soup.new_tag("h3")
        notes_title.string = "👨‍🍳 Notes du Chef"
        notes_section.append(notes_title)

        # Handle both string and list inputs
        if isinstance(chef_notes, list):
            notes_list = soup.new_tag("ul", class_="notes-list")
            for note in chef_notes:
                note_item = soup.new_tag("li")
                note_item.string = str(note)
                notes_list.append(note_item)
            notes_section.append(notes_list)
        else:
            notes_content = soup.new_tag("p")
            notes_content.string = str(chef_notes)
            notes_section.append(notes_content)

        container.append(notes_section)

    def _add_nutritional_info(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add nutritional information if available."""
        nutritional_info = data.get("nutritional_info", "")
        if not nutritional_info:
            return

        nutrition_section = soup.new_tag("section", class_="nutritional-info")

        nutrition_title = soup.new_tag("h3")
        nutrition_title.string = "🥗 Information Nutritionnelle"
        nutrition_section.append(nutrition_title)

        # Handle both string and dictionary inputs
        if isinstance(nutritional_info, dict):
            nutrition_list = soup.new_tag("ul", class_="nutrition-list")
            for key, value in nutritional_info.items():
                nutrition_item = soup.new_tag("li")
                nutrition_item.string = f"{key.replace('_', ' ').title()}: {value}"
                nutrition_list.append(nutrition_item)
            nutrition_section.append(nutrition_list)
        else:
            nutrition_content = soup.new_tag("p")
            nutrition_content.string = str(nutritional_info)
            nutrition_section.append(nutrition_content)

        container.append(nutrition_section)
