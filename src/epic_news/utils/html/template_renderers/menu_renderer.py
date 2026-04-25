"""
Menu Renderer

Renders menu planning data to structured HTML using BeautifulSoup.
Handles daily meal plans, ingredients, and nutritional information.
"""

from typing import Any

from bs4 import BeautifulSoup, Tag

from .base_renderer import BaseRenderer


class MenuRenderer(BaseRenderer):
    """Renders menu planning content with structured formatting."""

    def __init__(self) -> None:
        # No special initialisation needed currently
        pass

    def render(self, data: dict[str, Any]) -> str:
        """
        Render menu planning data to HTML.

        Args:
            data: Dictionary containing menu planning data

        Returns:
            HTML string for menu planning content
        """
        # Create main container
        soup = self.create_soup("div", class_="menu-planner")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add weekly overview if available
        self._add_weekly_overview(soup, container, data)

        # Add daily meal plans
        self._add_daily_plans(soup, container, data)

        # Add shopping list if available
        self._add_shopping_list(soup, container, data)

        # Add nutritional information if available
        self._add_nutritional_info(soup, container, data)


        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add menu planner header with title."""
        header = soup.new_tag("header", class_="menu-header")

        # Title
        title = data.get("title", "Menu Hebdomadaire")
        title_tag = soup.new_tag("h1", class_="menu-title")
        title_tag.string = f"🍽️ {title}"
        header.append(title_tag)

        # Date range if available
        date_range = data.get("date_range", "")
        if date_range:
            date_tag = soup.new_tag("p", class_="menu-date-range")
            date_tag.string = date_range
            header.append(date_tag)

        # Description if available
        description = data.get("description", "")
        if description:
            desc_tag = soup.new_tag("p", class_="menu-description")
            desc_tag.string = description
            header.append(desc_tag)

        container.append(header)

    def _add_weekly_overview(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add weekly menu overview if available."""
        overview = data.get("weekly_overview", "")
        if not overview:
            return

        overview_div = soup.new_tag("section", class_="menu-overview")

        overview_title = soup.new_tag("h2")
        overview_title.string = "📋 Aperçu de la semaine"
        overview_div.append(overview_title)

        overview_p = soup.new_tag("p")
        overview_p.string = overview
        overview_div.append(overview_p)

        container.append(overview_div)

    def _add_daily_plans(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add daily meal plans."""
        daily_plans = data.get("daily_plans", {})
        if not daily_plans:
            # Fallback to content if structured data not available
            content = data.get("content", "")
            if content:
                content_div = soup.new_tag("div", class_="menu-content")
                content_div.string = content
                container.append(content_div)
            return

        daily_plans_section = soup.new_tag("section", class_="daily-plans")

        plans_title = soup.new_tag("h2")
        plans_title.string = "🗓️ Menus Quotidiens"
        daily_plans_section.append(plans_title)

        # Iterate through each day's plan
        for day_dict in daily_plans:
            # Accept list of DailyMenu objects or dict with 'day'
            if isinstance(day_dict, dict) and "day" in day_dict:
                day_name = day_dict["day"]
                meals = {"lunch": day_dict.get("lunch"), "dinner": day_dict.get("dinner")}
            else:
                # Legacy mapping where key is day and value meals
                day_name, meals = day_dict
            day_div = self._create_day_plan(soup, day_name, meals)
            daily_plans_section.append(day_div)

        container.append(daily_plans_section)

    def _create_day_plan(self, soup: BeautifulSoup, day: str, meals: dict[str, Any]) -> Tag:
        """Create a daily meal plan card."""
        day_div = soup.new_tag("div", class_="day-plan")

        # Day header
        day_header = soup.new_tag("div", class_="day-header")

        # Add day emoji based on day name
        day_emoji = {
            "lundi": "1️⃣",
            "mardi": "2️⃣",
            "mercredi": "3️⃣",
            "jeudi": "4️⃣",
            "vendredi": "5️⃣",
            "samedi": "6️⃣",
            "dimanche": "7️⃣",
            "monday": "1️⃣",
            "tuesday": "2️⃣",
            "wednesday": "3️⃣",
            "thursday": "4️⃣",
            "friday": "5️⃣",
            "saturday": "6️⃣",
            "sunday": "7️⃣",
        }.get(day.lower(), "🗓️")

        day_title = soup.new_tag("h3")
        day_title.string = f"{day_emoji} {day}"
        day_header.append(day_title)

        day_div.append(day_header)

        # Meals container
        meals_div = soup.new_tag("div", class_="day-meals")

        # Standard meal types and their emojis
        meal_types = {
            "breakfast": "🍳 Petit-déjeuner",
            "lunch": "🥗 Déjeuner",
            "dinner": "🍲 Dîner",
            "snacks": "🍎 Collations",
            "petit-dejeuner": "🍳 Petit-déjeuner",
            "petit-déjeuner": "🍳 Petit-déjeuner",
            "dejeuner": "🥗 Déjeuner",
            "déjeuner": "🥗 Déjeuner",
            "diner": "🍲 Dîner",
            "dîner": "🍲 Dîner",
            "collations": "🍎 Collations",
        }

        if isinstance(meals, dict):
            # Create sections for each meal type
            for meal_type, meal_content in meals.items():
                meal_div = soup.new_tag("div", class_="meal")

                meal_name = meal_types.get(meal_type.lower(), f"🍽️ {meal_type}")
                meal_type_h4 = soup.new_tag("h4", class_="meal-type")
                meal_type_h4.string = meal_name
                meal_div.append(meal_type_h4)

                if isinstance(meal_content, list):
                    # Create list of dishes
                    dishes_list = soup.new_tag("ul", class_="dishes-list")
                    for dish in meal_content:
                        dish_item = soup.new_tag("li", class_="dish-item")
                        dish_item.string = dish
                        dishes_list.append(dish_item)
                    meal_div.append(dishes_list)
                else:
                    # Handle new 'dishes' array format or old structured meal format
                    if isinstance(meal_content, dict) and "dishes" in meal_content:
                        # New format: meal_content = {"dishes": [{"name": "...", "dish_type": "..."}]}
                        dishes_list = soup.new_tag("ul", class_="dishes-list")
                        dishes = meal_content.get("dishes", [])

                        # Map dish types to emojis
                        dish_type_emojis = {
                            "entrée": "🥗",
                            "plat principal": "🍽️",
                            "dessert": "🍮",
                            "starter": "🥗",
                            "main_course": "🍽️",
                            "main course": "🍽️",
                        }

                        for dish in dishes:
                            if isinstance(dish, dict):
                                dish_name = dish.get("name", "")
                                dish_type = dish.get("dish_type", "").lower()

                                if dish_name:
                                    dish_li = soup.new_tag("li", class_="dish-item")
                                    emoji = dish_type_emojis.get(dish_type, "🍽️")
                                    # Capitalize dish type for display
                                    display_type = dish_type.capitalize() if dish_type else "Plat"
                                    dish_li.string = f"{emoji} {display_type}: {dish_name}"
                                    dishes_list.append(dish_li)

                        meal_div.append(dishes_list)

                    elif isinstance(meal_content, dict) and any(
                        k in meal_content for k in ("starter", "main_course", "dessert")
                    ):
                        # Old format: backward compatibility
                        sub_dishes_ul = soup.new_tag("ul", class_="dishes-list")
                        sub_map = {
                            "starter": "🥗 Entrée",
                            "main_course": "🍽️ Plat principal",
                            "dessert": "🍮 Dessert",
                        }
                        for sub_key, label in sub_map.items():
                            sub_val = meal_content.get(sub_key)
                            if not sub_val:
                                continue
                            dish_li = soup.new_tag("li", class_="dish-item")
                            if isinstance(sub_val, dict):
                                dish_name = sub_val.get("name") or str(sub_val)
                            else:
                                dish_name = str(sub_val)
                            dish_li.string = f"{label}: {dish_name}"
                            sub_dishes_ul.append(dish_li)
                        meal_div.append(sub_dishes_ul)
                    else:
                        # Single dish or text description
                        meal_text = soup.new_tag("p", class_="meal-text")
                        meal_text.string = str(meal_content)
                        meal_div.append(meal_text)

                meals_div.append(meal_div)
        elif isinstance(meals, list):
            # Simple list of meals for the day
            dishes_list = soup.new_tag("ul", class_="dishes-list")
            for meal in meals:
                dish_item = soup.new_tag("li", class_="dish-item")
                dish_item.string = meal
                dishes_list.append(dish_item)
            meals_div.append(dishes_list)
        else:
            # Plain text content
            meal_text = soup.new_tag("p", class_="meal-text")
            meal_text.string = str(meals)
            meals_div.append(meal_text)

        day_div.append(meals_div)
        return day_div

    def _add_shopping_list(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add shopping list if available."""
        shopping_list = data.get("shopping_list", [])
        if not shopping_list:
            return

        shopping_section = soup.new_tag("section", class_="shopping-list")

        shopping_title = soup.new_tag("h2")
        shopping_title.string = "🛒 Liste de courses"
        shopping_section.append(shopping_title)

        # Group items by category if the data is structured that way
        if isinstance(shopping_list, dict):
            for category, items in shopping_list.items():
                category_div = soup.new_tag("div", class_="shopping-category")

                category_title = soup.new_tag("h3")
                category_title.string = category
                category_div.append(category_title)

                items_list = soup.new_tag("ul")
                for item in items:
                    item_li = soup.new_tag("li")
                    item_li.string = item
                    items_list.append(item_li)

                category_div.append(items_list)
                shopping_section.append(category_div)
        else:
            # Simple list of items
            items_list = soup.new_tag("ul")
            for item in shopping_list:
                item_li = soup.new_tag("li")
                item_li.string = item
                items_list.append(item_li)

            shopping_section.append(items_list)

        container.append(shopping_section)

    def _add_nutritional_info(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add nutritional information if available."""
        nutrition = data.get("nutritional_info", {})
        if not nutrition:
            return

        nutrition_section = soup.new_tag("section", class_="nutritional-info")

        nutrition_title = soup.new_tag("h2")
        nutrition_title.string = "🥗 Information Nutritionnelle"
        nutrition_section.append(nutrition_title)

        if isinstance(nutrition, dict):
            # Detailed nutritional information
            nutrition_table = soup.new_tag("table", class_="nutrition-table")

            # Table header
            thead = soup.new_tag("thead")
            tr = soup.new_tag("tr")

            th_nutrient = soup.new_tag("th")
            th_nutrient.string = "Nutriment"
            tr.append(th_nutrient)

            th_value = soup.new_tag("th")
            th_value.string = "Valeur"
            tr.append(th_value)

            thead.append(tr)
            nutrition_table.append(thead)

            # Table body
            tbody = soup.new_tag("tbody")
            for nutrient, value in nutrition.items():
                tr = soup.new_tag("tr")

                td_nutrient = soup.new_tag("td")
                td_nutrient.string = nutrient
                tr.append(td_nutrient)

                td_value = soup.new_tag("td")
                td_value.string = str(value)
                tr.append(td_value)

                tbody.append(tr)

            nutrition_table.append(tbody)
            nutrition_section.append(nutrition_table)
        else:
            # Simple text information
            nutrition_p = soup.new_tag("p")
            nutrition_p.string = str(nutrition)
            nutrition_section.append(nutrition_p)

        container.append(nutrition_section)
