import zipfile

from epic_news.models.crews.shopping_advice_report import (
    CompetitorInfo,
    PriceInfo,
    ProductInfo,
    ShoppingAdviceOutput,
)
from epic_news.utils.docx_report.crews.shopping import assemble_shopping_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_shopping_docx(tmp_path):
    model = ShoppingAdviceOutput(
        product_info=ProductInfo(
            name="Casque-XYZ",
            overview="Un casque.",
            key_specifications=["Bluetooth 5.3"],
            pros=["Confort"],
            cons=["Prix"],
            target_audience="Audiophiles",
            common_issues=["Bug-Appairage"],
        ),
        switzerland_prices=[
            PriceInfo(
                retailer="Digitec",
                price="299 CHF",
                url=None,
                shipping_cost=None,
                total_cost="299 CHF",
                notes=None,
            )
        ],
        france_prices=[
            PriceInfo(
                retailer="Fnac",
                price="279 EUR",
                url=None,
                shipping_cost="0 EUR",
                total_cost="279 EUR",
                notes="Stock-limité",
            )
        ],
        competitors=[
            CompetitorInfo(
                name="Concurrent-A",
                price_range="250-300",
                key_features=["ANC", "30h"],
                pros=["Léger"],
                cons=["Fragile"],
                target_audience="Sport",
            )
        ],
        executive_summary="ES",
        final_recommendations="FR",
        best_deals=["Offre-Alpha"],
        user_preferences_context="ctx",
    )
    llm = _StubLLM()
    out = assemble_shopping_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "shopping.docx"), llm)
    txt = _text(out)

    for figure in [
        "Casque-XYZ",
        "Digitec",
        "299 CHF",
        "Concurrent-A",
        "Offre-Alpha",
        "Bug-Appairage",
        "Léger",
        "Fragile",
        "Stock-limité",
    ]:
        assert figure in txt, f"missing verbatim figure: {figure}"

    assert "ANC; 30h" in txt, "key_features must be joined, not stringified as a list"
    assert "['ANC'" not in txt, "key_features must not be stringified as a Python list"

    assert "None" not in txt, "unguarded None leaked into the document"

    # only Résumé + Recommandations narrate; the rest are deterministic
    assert llm.calls == 2

    headings = [
        "Résumé",
        "Produit",
        "Prix Suisse",
        "Prix France",
        "Concurrents",
        "Meilleures offres",
        "Recommandations",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
