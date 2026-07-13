"""SHOPPING → DOCX: narrated summary/recommendations + deterministic product/price/competitor tables."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.shopping_advice_report import ShoppingAdviceOutput
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.docx_report.tables import md_table

_PERSONA = (
    "Tu es un conseiller d'achat. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)

_PRICE_COLUMNS = [
    ("Détaillant", "retailer"),
    ("Prix", "price"),
    ("Livraison", "shipping"),
    ("Total", "total"),
    ("Notes", "notes"),
]

_COMPETITOR_COLUMNS = [
    ("Produit", "name"),
    ("Gamme de prix", "range"),
    ("Caractéristiques", "features"),
    ("Avantages", "pros"),
    ("Inconvénients", "cons"),
    ("Public cible", "audience"),
]


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def _price_rows(prices: list) -> list[dict]:
    return [
        {
            "retailer": p.retailer,
            "price": p.price,
            "shipping": p.shipping_cost or "—",
            "total": p.total_cost or "—",
            "notes": p.notes or "—",
        }
        for p in prices
    ]


def assemble_shopping_docx(
    model: ShoppingAdviceOutput, inputs: dict, output_path: str, llm: Any = None
) -> str:
    """Build the SHOPPING report as a DOCX: narrated prose + deterministic product/price/competitor tables."""
    llm = llm or LLMConfig.get_openrouter_llm()
    pi = model.product_info

    product_body = (
        f"{pi.overview}\n\n"
        f"**Spécifications :**\n{_bullets(pi.key_specifications)}\n\n"
        f"**Avantages :**\n{_bullets(pi.pros)}\n\n"
        f"**Inconvénients :**\n{_bullets(pi.cons)}\n\n"
        f"**Public cible :** {pi.target_audience}"
        f"\n\n**Problèmes connus :**\n{_bullets(pi.common_issues)}"
    )

    competitor_rows = [
        {
            "name": c.name,
            "range": c.price_range,
            "features": "; ".join(c.key_features),
            "pros": "; ".join(c.pros),
            "cons": "; ".join(c.cons),
            "audience": c.target_audience,
        }
        for c in model.competitors
    ]

    sections = [
        Section(
            "Résumé",
            instruction="Reformule le résumé en prose fluide.",
            context=model.executive_summary or "",
        ),
        Section("Produit", body=product_body),
        Section("Prix Suisse", body=md_table(_price_rows(model.switzerland_prices), _PRICE_COLUMNS)),
        Section("Prix France", body=md_table(_price_rows(model.france_prices), _PRICE_COLUMNS)),
        Section("Concurrents", body=md_table(competitor_rows, _COMPETITOR_COLUMNS)),
        Section("Meilleures offres", body=_bullets(model.best_deals)),
        Section(
            "Recommandations",
            instruction="Reformule les recommandations en prose fluide.",
            context=model.final_recommendations or "",
        ),
    ]
    meta = {
        "title": pi.name or "Conseil d'achat",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
