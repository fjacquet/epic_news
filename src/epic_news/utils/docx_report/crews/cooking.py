"""COOKING → DOCX: deterministic recipe fidelity (quantities/steps verbatim) + narrated notes.

Fidelity-critical: ingredients and directions are text blocks that must survive
verbatim, split line-by-line. The LLM is NEVER used to rewrite them — only the
optional Notes section is narrated.
"""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.docx_report.tables import md_table

_PERSONA = (
    "Tu es un chef cuisinier. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Ne modifie JAMAIS les quantités ni les étapes."
)


def _ingredients_block(ingredients: str) -> str:
    """Deterministic bullet list, one line per ingredient, verbatim quantities."""
    lines = [f"- {ln.strip()}" for ln in ingredients.splitlines() if ln.strip()]
    return "\n".join(lines) if lines else "_Aucun ingrédient._"


def _directions_block(directions: str) -> str:
    """Deterministic step list, one paragraph per step, verbatim text."""
    lines = [ln.strip() for ln in directions.splitlines() if ln.strip()]
    return "\n\n".join(lines) if lines else "_Aucune étape._"


def assemble_cooking_docx(model: PaprikaRecipe, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the COOKING report as a DOCX: deterministic recipe + narrated notes."""
    llm = llm or LLMConfig.get_openrouter_llm()
    info_rows = [
        {"champ": "Portions", "valeur": model.servings or "—"},
        {"champ": "Préparation", "valeur": model.prep_time or "—"},
        {"champ": "Cuisson", "valeur": model.cook_time or "—"},
        {"champ": "Difficulté", "valeur": model.difficulty or "—"},
        {"champ": "Catégories", "valeur": ", ".join(model.categories) or "—"},
    ]
    sections: list[Section] = [
        Section("Informations", body=md_table(info_rows, [("Champ", "champ"), ("Valeur", "valeur")])),
        Section("Ingrédients", body=_ingredients_block(model.ingredients)),
        Section("Préparation", body=_directions_block(model.directions)),
    ]
    if model.notes:
        sections.append(
            Section(
                "Notes",
                instruction="Reformule les notes en prose.",
                context=model.notes,
            )
        )
    meta = {
        "title": model.name or "Recette",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
