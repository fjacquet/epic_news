"""MENU → DOCX: deterministic weekly plan fidelity (dish names verbatim) + narrated prose.

Fidelity-critical: the deeply nested weekly plan (daily menus → meals → dishes)
is rendered verbatim from the Pydantic model — the LLM is NEVER used to touch
dish names, descriptions, or ingredients. Only the analytical sections
(nutritional balance, gustative coherence, adaptations) are narrated.
"""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.menu_designer_report import DailyMenu, DishInfo, WeeklyMenuPlan
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un concepteur de menus. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Ne modifie JAMAIS les noms de plats ni les ingrédients."
)


def _dish_line(role: str, dish: DishInfo | None) -> str:
    """Deterministic dish line: verbatim name/description, guarded against None dessert."""
    if dish is None:
        return f"- **{role} :** —"
    line = f"- **{role} :** {dish.name} — {dish.description}"
    if dish.seasonal_ingredients:
        line += f" _(Ingrédients : {', '.join(dish.seasonal_ingredients)})_"
    return line


def _day_block(dm: DailyMenu) -> str:
    """Deterministic Markdown block for one day: lunch and dinner dish lines."""
    lunch_lines = "\n".join(
        [
            _dish_line("Entrée", dm.lunch.starter),
            _dish_line("Plat principal", dm.lunch.main_course),
            _dish_line("Dessert", dm.lunch.dessert),
        ]
    )
    dinner_lines = "\n".join(
        [
            _dish_line("Entrée", dm.dinner.starter),
            _dish_line("Plat principal", dm.dinner.main_course),
            _dish_line("Dessert", dm.dinner.dessert),
        ]
    )
    return f"## {dm.day} — {dm.date}\n\n**Déjeuner**\n{lunch_lines}\n\n**Dîner**\n{dinner_lines}"


def assemble_menu_docx(model: WeeklyMenuPlan, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the MENU report as a DOCX: deterministic weekly plan + narrated analysis."""
    llm = llm or LLMConfig.get_openrouter_llm()
    daily_menus_body = (
        "\n\n".join(_day_block(dm) for dm in model.daily_menus) if model.daily_menus else "_Aucun menu._"
    )
    sections: list[Section] = [
        Section(
            "Aperçu",
            body=f"Semaine du {model.week_start_date} — Saison : {model.season}.",
        ),
        Section("Menus quotidiens", body=daily_menus_body),
        Section(
            "Équilibre nutritionnel",
            instruction="Reformule l'équilibre nutritionnel en prose fluide.",
            context=model.nutritional_balance,
        ),
        Section(
            "Cohérence gustative",
            instruction="Reformule la cohérence gustative en prose fluide.",
            context=model.gustative_coherence,
        ),
        Section(
            "Adaptations",
            instruction="Reformule les adaptations aux contraintes et préférences en prose fluide.",
            context=f"{model.constraints_adaptation}\n\n{model.preferences_integration}",
        ),
    ]
    meta = {
        "title": f"Menu de la semaine du {model.week_start_date}",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
