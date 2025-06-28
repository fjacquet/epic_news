"""
Utilitaires pour la génération de chemins de fichiers HTML.

Ce module contient des fonctions utilitaires pour extraire des informations
des données d'état et générer des chemins de fichiers HTML appropriés.
"""

import json
from typing import Any

from epic_news.utils.string_utils import create_topic_slug


def extract_recipe_title_from_state(state_data: dict[str, Any]) -> str | None:
    """Extrait le titre de la recette à partir des données d'état.

    Args:
        state_data: Données d'état contenant les informations de la recette

    Returns:
        Le titre de la recette ou None si non trouvé
    """
    # Initialiser les données de recette
    recipe_data = {}

    # Cas 1: Les données sont dans state_data["recipe"]["raw"]
    if "recipe" in state_data and "raw" in state_data["recipe"]:
        recipe_raw = state_data["recipe"]["raw"]
        try:
            recipe_data = json.loads(recipe_raw) if isinstance(recipe_raw, str) else recipe_raw
        except Exception:
            pass

    # Cas 2: Chercher dans d'autres clés de state_data
    if not recipe_data:
        for key, value in state_data.items():
            if isinstance(value, dict) and any(field in value for field in ["name", "title", "recipe_title"]):
                recipe_data = value
                break

    # Extraire le titre des données de recette
    for field in ["name", "recipe_title", "title"]:
        if field in recipe_data and recipe_data[field]:
            return recipe_data[field]

    return None


def generate_cooking_output_path(state_data: dict[str, Any]) -> str:
    """Génère le chemin de sortie pour une recette de cuisine.

    Args:
        state_data: Données d'état contenant les informations de la recette

    Returns:
        Le chemin de sortie pour le fichier HTML
    """
    # Extraire le titre de la recette
    recipe_title = extract_recipe_title_from_state(state_data)

    # Si on a un titre, générer un slug
    if recipe_title:
        slug = create_topic_slug(recipe_title)

        # Vérifier que le slug n'est pas vide
        if not slug or slug.isspace():
            print(f"  ⚠️ Slug vide généré pour '{recipe_title}', utilisation d'un slug par défaut")
            slug = "recette-cuisine"

        print(f"  🔍 Génération du nom de fichier: output/cooking/{slug}.html")
        return f"output/cooking/{slug}.html"

    # Fallback si pas de titre
    print("  ⚠️ Pas de titre trouvé, utilisation du nom de fichier par défaut")
    return "output/cooking/recette-cuisine.html"


def determine_output_path(selected_crew: str, state_data: dict[str, Any] = None) -> str:
    """Determine the appropriate output path based on selected crew category

    Si state_data.output_file existe, on utilise ce chemin en remplaçant l'extension par .html
    Sinon, on utilise un chemin basé sur le contenu (titre de la recette, etc.)

    Args:
        selected_crew: Catégorie du crew sélectionné
        state_data: Données d'état contenant les informations

    Returns:
        Le chemin de sortie pour le fichier HTML
    """
    # Si on a un output_file dans state_data, on l'utilise en remplaçant l'extension par .html
    if state_data and "output_file" in state_data and state_data["output_file"]:
        yaml_path = state_data["output_file"]
        # Vérifier que le chemin n'est pas vide ou juste un point
        if not yaml_path or yaml_path.strip() in [".", ""]:
            print("  ⚠️ output_file vide ou invalide, utilisation du chemin par défaut")
        else:
            # Si le chemin se termine déjà par .html, le retourner tel quel
            if yaml_path.endswith(".html"):
                return yaml_path
            # Remplacer l'extension par .html
            if yaml_path.endswith((".yaml", ".yml", ".json")):
                return yaml_path.rsplit(".", 1)[0] + ".html"
            # Si pas d'extension reconnue, ajouter .html
            return yaml_path + ".html"

    # Pour le cas spécifique de COOKING, utiliser une méthode dédiée
    if selected_crew == "COOKING" and state_data:
        return generate_cooking_output_path(state_data)

    # Fallback sur les chemins par défaut pour les autres crews
    output_paths = {
        "POEM": "output/poem/poem.html",
        "FINDAILY": "output/findaily/report.html",
        "NEWSDAILY": "output/news_daily/report.html",
        "SAINT": "output/saint_daily/report.html",
        "SHOPPING": "output/shopping/advice.html",
        "LIBRARY": "output/library/summary.html",
        "MEETING_PREP": "output/meeting_prep/prep.html",
        "HOLIDAY_PLANNER": "output/holiday_planner/plan.html",
        "MENU": "output/menu_designer/menu.html",
        "NEWSCOMPANY": "output/news/report.html",
        "RSS": "output/rss_weekly/report.html",
        "MARKETING_WRITERS": "output/marketing/content.html",
        "SALES_PROSPECTING": "output/sales_prospecting/report.html",
        "OPEN_SOURCE_INTELLIGENCE": "output/osint/report.html",
    }

    return output_paths.get(selected_crew, f"output/{selected_crew.lower()}/report.html")
