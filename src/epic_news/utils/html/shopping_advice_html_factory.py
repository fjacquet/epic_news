"""
Factory function for converting ShoppingAdviceOutput to HTML using the universal template system.
"""

from __future__ import annotations

from epic_news.models.shopping_advice_models import ShoppingAdviceOutput
from epic_news.utils.html.template_manager import TemplateManager


def shopping_advice_to_html(
    shopping_advice: ShoppingAdviceOutput, topic: str = "", html_file: str | None = None
) -> str:
    """
    Convert a ShoppingAdviceOutput instance to a complete HTML document using the universal template system.

    Args:
        shopping_advice (ShoppingAdviceOutput): The shopping advice model to render.
        topic (str): The topic or product being researched (optional).
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """

    # Create rich, structured content data that matches TemplateManager expectations
    content_data = {
        # Basic info
        "title": f"Guide d'achat : {shopping_advice.product_info.name}",
        "topic": topic or shopping_advice.product_info.name,
        "executive_summary": shopping_advice.executive_summary,
        "user_preferences_and_constraints": shopping_advice.user_preferences_context,
        # Product information (matching TemplateManager field names)
        "product_name": shopping_advice.product_info.name,
        "product_overview": shopping_advice.product_info.overview,
        "product_specifications": shopping_advice.product_info.key_specifications,
        "product_pros": shopping_advice.product_info.pros,
        "product_cons": shopping_advice.product_info.cons,
        "target_audience": shopping_advice.product_info.target_audience,
        "common_issues": shopping_advice.product_info.common_issues,
        # Pricing data (as objects, not HTML strings)
        "switzerland_prices": [
            {
                "retailer": p.retailer,
                "price": p.price,
                "url": p.url,
                "shipping_cost": p.shipping_cost,
                "total_cost": p.total_cost,
                "notes": p.notes,
            }
            for p in shopping_advice.switzerland_prices
        ],
        "france_prices": [
            {
                "retailer": p.retailer,
                "price": p.price,
                "url": p.url,
                "shipping_cost": p.shipping_cost,
                "total_cost": p.total_cost,
                "notes": p.notes,
            }
            for p in shopping_advice.france_prices
        ],
        # Competitors data (as objects, not HTML strings)
        "competitors": [
            {
                "name": c.name,
                "price_range": c.price_range,
                "key_features": c.key_features,
                "pros": c.pros,
                "cons": c.cons,
                "target_audience": c.target_audience,
            }
            for c in shopping_advice.competitors
        ],
        # Additional rich content
        "best_deals": shopping_advice.best_deals,
        "final_recommendations": shopping_advice.final_recommendations,
        # Metadata for enhanced presentation
        "product_category": "Machine à eau pétillante"
        if "sparkling" in shopping_advice.product_info.name.lower()
        else "Produit",
        "analysis_date": "2024-06-30",
        "currency_ch": "CHF",
        "currency_fr": "EUR",
        "total_competitors": len(shopping_advice.competitors),
        "total_retailers_ch": len(shopping_advice.switzerland_prices),
        "total_retailers_fr": len(shopping_advice.france_prices),
    }

    template_manager = TemplateManager()
    html = template_manager.render_report("SHOPPING_ADVICE", content_data)

    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

    return html
