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

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recipe header with title and description."""
        header = soup.new_tag("header", class_="recipe-header")

        # Recipe title
        title = data.get("recipe_title", "Recette")
        title_tag = soup.new_tag("h1", class_="recipe-title")
        title_tag.string = f"🍽️ {title}"
        header.append(title_tag)

        # Recipe description if available
        description = data.get("description", "")
        if description:
            desc_tag = soup.new_tag("p", class_="recipe-description")
            desc_tag.string = description
            header.append(desc_tag)

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
        """Add chef's notes if available."""
        chef_notes = data.get("chef_notes", "")
        if not chef_notes:
            return

        notes_section = soup.new_tag("section", class_="chef-notes")

        notes_title = soup.new_tag("h3")
        notes_title.string = "👨‍🍳 Notes du Chef"
        notes_section.append(notes_title)

        notes_content = soup.new_tag("p")
        notes_content.string = chef_notes
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

        nutrition_content = soup.new_tag("p")
        nutrition_content.string = nutritional_info
        nutrition_section.append(nutrition_content)

        container.append(nutrition_section)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles to the recipe."""
        style = soup.new_tag("style")
        style.string = """
        .recipe-container {
            max-width: 800px;
            margin: 0 auto;
            font-family: var(--body-font);
            color: var(--text-color);
        }
        .recipe-header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--accent-color);
        }
        .recipe-title {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }
        .recipe-description {
            font-style: italic;
            color: var(--text-muted);
        }
        .recipe-meta {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-around;
            margin: 1.5rem 0;
            padding: 1rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .meta-item {
            margin: 0.5rem 1rem;
        }
        .recipe-ingredients, .recipe-instructions, .chef-notes, .nutritional-info {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .recipe-ingredients h2, .recipe-instructions h2, .chef-notes h3, .nutritional-info h3 {
            color: var(--heading-color);
            margin-top: 0;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .ingredients-list {
            list-style-type: none;
            padding-left: 0.5rem;
        }
        .ingredients-list li {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: rgba(0,0,0,0.05);
            border-radius: 4px;
        }
        .instructions-list {
            padding-left: 1.5rem;
        }
        .instructions-list li {
            margin: 1rem 0;
            padding: 0.5rem;
        }
        """
        soup.append(style)
