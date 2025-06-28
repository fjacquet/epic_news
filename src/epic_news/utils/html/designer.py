"""
Utility functions for HtmlDesignerCrew - Template selection and HTML generation.
"""

import json
from datetime import datetime
from typing import Any

from .template_utils import render_universal_report


def select_template_for_report(state_data: dict[str, Any]) -> str:
    """
    Intelligently select the most appropriate template based on report content.

    Args:
        state_data: Application state data containing crew results

    Returns:
        Template name to use for rendering
    """
    # For now, we'll use the universal template as it's the most flexible
    # Future enhancement: Add logic to select specific templates based on content type
    return "universal_report_template.html"


def analyze_state_data(state_json: str) -> dict[str, Any]:
    """
    Analyze the application state data to extract key information for HTML generation.

    Args:
        state_json: JSON string containing the application state

    Returns:
        Dictionary with analyzed data structure
    """
    try:
        state_data = json.loads(state_json)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data", "sections": []}

    analysis = {
        "report_type": state_data.get("report_type", "daily"),
        "sections": [],
        "key_metrics": {},
        "recommendations": [],
        "data_sources": [],
    }

    # Analyze crew results
    crew_results = state_data.get("crew_results", {})

    # Financial data analysis
    if "findaily" in crew_results or "fin_daily" in crew_results:
        analysis["sections"].append(
            {
                "type": "finance",
                "title": "📈 Analyse Financière",
                "priority": 1,
                "data": crew_results.get("findaily") or crew_results.get("fin_daily"),
            }
        )

    # News analysis
    if "news_daily" in crew_results:
        analysis["sections"].append(
            {
                "type": "news",
                "title": "📰 Actualités du Jour",
                "priority": 2,
                "data": crew_results.get("news_daily"),
            }
        )

    # Cooking/Recipe analysis
    if "cooking" in crew_results:
        analysis["sections"].append(
            {
                "type": "cooking",
                "title": "👨‍🍳 Recette du Jour",
                "priority": 3,
                "data": crew_results.get("cooking"),
            }
        )

    # Saint of the day
    if "saint_daily" in crew_results:
        analysis["sections"].append(
            {
                "type": "saint",
                "title": "⛪ Saint du Jour",
                "priority": 4,
                "data": crew_results.get("saint_daily"),
            }
        )

    # Sort sections by priority
    analysis["sections"].sort(key=lambda x: x.get("priority", 999))

    return analysis


def generate_html_content(analysis: dict[str, Any]) -> str:
    """
    Generate professional HTML content based on the analyzed data.

    Args:
        analysis: Analyzed data structure from analyze_state_data

    Returns:
        HTML content string ready for template rendering
    """
    html_parts = []

    # Executive Summary
    html_parts.append("""
    <section class="executive-summary">
        <h2>📋 Résumé Exécutif</h2>
        <p>Ce rapport quotidien consolide les informations essentielles de nos différentes équipes d'analyse 
        pour vous fournir une vue d'ensemble complète et actionnable.</p>
    </section>
    """)

    # Process each section
    for section in analysis.get("sections", []):
        section_html = generate_section_html(section)
        if section_html:
            html_parts.append(section_html)

    # Conclusions and recommendations
    if analysis.get("recommendations"):
        html_parts.append("""
        <section class="recommendations">
            <h2>💡 Recommandations</h2>
            <ul>
        """)
        for rec in analysis["recommendations"]:
            html_parts.append(f"<li>{rec}</li>")
        html_parts.append("</ul></section>")

    # Footer with methodology
    html_parts.append("""
    <section class="methodology">
        <h2>📊 Méthodologie</h2>
        <p>Ce rapport est généré automatiquement par notre système d'intelligence artificielle Epic News, 
        qui analyse et consolide les données de multiples sources pour fournir des insights pertinents et actionnables.</p>
        <p><strong>Sources de données :</strong> Analyses financières, actualités, recommandations culinaires, 
        et informations culturelles.</p>
    </section>
    """)

    return "\n".join(html_parts)


def generate_section_html(section: dict[str, Any]) -> str:
    """
    Generate HTML for a specific section based on its type.

    Args:
        section: Section data with type, title, and data

    Returns:
        HTML string for the section
    """
    section_type = section.get("type", "generic")
    title = section.get("title", "Section")
    data = section.get("data", {})

    if section_type == "finance":
        return generate_finance_section_html(title, data)
    if section_type == "news":
        return generate_news_section_html(title, data)
    if section_type == "cooking":
        return generate_cooking_section_html(title, data)
    if section_type == "saint":
        return generate_saint_section_html(title, data)
    return generate_generic_section_html(title, data)


def generate_finance_section_html(title: str, data: Any) -> str:
    """Generate HTML for financial analysis section."""
    return f"""
    <section class="finance-section">
        <h2>{title}</h2>
        <div class="finance-content">
            <p>📊 <strong>Analyse des marchés financiers :</strong></p>
            <div class="financial-highlights">
                <p>Les données financières ont été analysées pour identifier les tendances clés et opportunités d'investissement.</p>
                <p>🔍 <strong>Points clés :</strong> Surveillance continue des marchés actions, crypto-monnaies et indicateurs économiques.</p>
            </div>
        </div>
    </section>
    """


def generate_news_section_html(title: str, data: Any) -> str:
    """Generate HTML for news analysis section."""
    return f"""
    <section class="news-section">
        <h2>{title}</h2>
        <div class="news-content">
            <p>📰 <strong>Actualités du jour :</strong></p>
            <div class="news-highlights">
                <p>Analyse des principales actualités et leur impact potentiel sur les marchés et la société.</p>
                <p>🌍 <strong>Focus :</strong> Événements économiques, politiques et sociaux significatifs.</p>
            </div>
        </div>
    </section>
    """


def generate_cooking_section_html(title: str, data: Any) -> str:
    """Generate HTML for cooking/recipe section."""
    return f"""
    <section class="cooking-section">
        <h2>{title}</h2>
        <div class="cooking-content">
            <p>👨‍🍳 <strong>Recommandation culinaire :</strong></p>
            <div class="recipe-highlights">
                <p>Découvrez notre sélection culinaire du jour, préparée avec soin pour vous inspirer en cuisine.</p>
                <p>🍽️ <strong>Conseil :</strong> Recettes équilibrées et savoureuses pour tous les goûts.</p>
            </div>
        </div>
    </section>
    """


def generate_saint_section_html(title: str, data: Any) -> str:
    """Generate HTML for saint of the day section."""
    return f"""
    <section class="saint-section">
        <h2>{title}</h2>
        <div class="saint-content">
            <p>⛪ <strong>Saint du jour :</strong></p>
            <div class="saint-highlights">
                <p>Découvrez l'histoire et les enseignements du saint célébré aujourd'hui.</p>
                <p>🙏 <strong>Inspiration :</strong> Réflexions spirituelles et culturelles.</p>
            </div>
        </div>
    </section>
    """


def generate_generic_section_html(title: str, data: Any) -> str:
    """Generate HTML for generic sections."""
    return f"""
    <section class="generic-section">
        <h2>{title}</h2>
        <div class="section-content">
            <p>Informations analysées et consolidées pour votre information.</p>
        </div>
    </section>
    """


def render_professional_report(
    state_json: str, report_type: str = "daily", custom_title: str | None = None
) -> str:
    """
    Main function to render a professional HTML report from state data.

    Args:
        state_json: JSON string containing application state
        report_type: Type of report (daily, weekly, etc.)
        custom_title: Optional custom title for the report

    Returns:
        Complete HTML report string
    """
    # Analyze the state data
    analysis = analyze_state_data(state_json)

    # Generate HTML content
    html_content = generate_html_content(analysis)

    # Determine report title
    if custom_title:
        title = custom_title
    else:
        date_str = datetime.now().strftime("%d/%m/%Y")
        title = f"Epic News - Rapport {report_type.title()} du {date_str}"

    # Render using universal template
    return render_universal_report(
        title=title, content=html_content, generation_date=datetime.now().strftime("%d/%m/%Y à %H:%M")
    )
