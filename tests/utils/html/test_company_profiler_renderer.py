"""Tests for the Company Profiler HTML renderer.

Renders through the public path (``TemplateManager.render_report``) using the
``COMPANY_PROFILE`` crew identifier registered in ``renderer_factory.py``, and
asserts on content actually fed into the data dict to exercise the renderer's
real branch logic (sections, cards, lists, tables, and empty-state guards).
"""

from epic_news.models.crews.company_profiler_report import (
    CompanyCoreInfo,
    CompanyHistory,
    CompanyProfileReport,
    Financials,
    LegalCompliance,
    Management,
    MarketPosition,
    ProductsAndServices,
)
from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.company_profiler_renderer import (
    CompanyProfilerRenderer,
)

CREW_IDENTIFIER = "COMPANY_PROFILE"


def _full_report() -> CompanyProfileReport:
    """Build a fully-populated, valid CompanyProfileReport for rendering."""
    core_info = CompanyCoreInfo(
        legal_name="Exemple SA Legal Name",
        parent_company="Exemple Holding Group",
        subsidiaries=["Exemple Sub One", "Exemple Sub Two"],
        year_founded=1998,
        headquarters_location="Geneve, Suisse",
        industry_classification="Technologie Financiere",
        business_activities=["Paiements en ligne", "Conseil financier"],
        employee_count=4200,
        revenue=2_500_000_000,  # -> "2.5 Mrd €"
        market_cap=750_000_000,  # -> "750.0 M€"
        corporate_structure="Societe Anonyme",
        ownership_details="Detenue a 60% par la famille fondatrice",
        mission_statement="Rendre la finance accessible a tous.",
        core_values=["Integrite", "Innovation", "Transparence"],
    )

    history = CompanyHistory(
        key_milestones=["1998: Fondation a Geneve", "2010: Introduction en bourse"],
        founding_story="L'entreprise a ete fondee par trois ingenieurs en 1998.",
        strategic_shifts=["Virage vers le cloud en 2015"],
        acquisitions_and_mergers=[
            {"cible": "FinTech Absorbee", "annee": 2019},
        ],
        leadership_changes=[{"date": "2020", "role": "CEO"}],
        major_product_launches=["Plateforme Exemple Pay"],
        challenges_or_controversies=["Amende reglementaire en 2021"],
    )

    financials = Financials(
        revenue_and_profit_trends=[
            {"annee": 2021, "revenue": 2000000000, "profit": None},
            {"annee": 2022, "revenue": 2500000000, "profit": 300000000},
        ],
        key_financial_ratios={"marge_nette": "12%", "ratio_endettement": 0.45},
        funding_rounds=[{"round": "Series A", "amount": 5000000}],
        major_investors=["Fonds Alpha Capital", "Fonds Beta Ventures"],
        debt_structure={"dette_court_terme": "100M€", "dette_long_terme": "300M€"},
        recent_financial_news=["Resultats trimestriels en hausse de 8%"],
    )

    market_position = MarketPosition(
        market_share="18% du marche europeen",
        competitive_landscape="Marche fragmente avec 5 acteurs majeurs.",
        key_competitors=["Concurrent Un", "Concurrent Deux"],
        comparative_advantages=["Technologie proprietaire brevetee", "Reseau de distribution etendu"],
        industry_trends=["Digitalisation acceleree"],
        growth_opportunities=["Expansion en Asie du Sud-Est"],
        challenges=["Pression reglementaire croissante"],
    )

    products_and_services = ProductsAndServices(
        core_product_lines=["Exemple Pay", "Exemple Wallet"],
        recent_launches=["Exemple Pay Business"],
        discontinued_offerings=["Exemple Classic"],
        pricing_strategy="Modele freemium avec abonnement premium",
        customer_segments=["PME", "Grands comptes"],
    )

    management = Management(
        key_executives=[
            {"name": "Alice Dupont-Exemple", "role": "Directrice Generale"},
            {"nom": "Bernard Martin-Exemple", "titre": "Directeur Financier"},
            {"position": "Fallback Position Only"},
        ],
        board_of_directors=["Membre Conseil Un", "Membre Conseil Deux"],
        management_style="Style de gestion collaboratif",
        corporate_culture="Culture d'innovation et de transparence radicale",
    )

    legal_compliance = LegalCompliance(
        regulatory_framework="Regule par la FINMA en Suisse",
        compliance_history=["Audit reussi en 2022"],
        ongoing_litigation=["Litige en cours avec ExPartner Corp"],
        regulatory_filings=["Rapport annuel 2023"],
    )

    return CompanyProfileReport(
        company_name="Exemple Corp International",
        core_info=core_info,
        history=history,
        financials=financials,
        market_position=market_position,
        products_and_services=products_and_services,
        management=management,
        legal_compliance=legal_compliance,
    )


def test_company_profiler_full_data_renders_all_sections():
    """Full data set: every optional section/branch should render its content."""
    data = _full_report().model_dump()
    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    # Basic structure
    assert "<!DOCTYPE html>" in html
    assert "company-profiler-report" in html

    # Header
    assert "Exemple Corp International" in html

    # Core info grid + currency formatting branches (Mrd€, M€)
    assert "Exemple SA Legal Name" in html
    assert "Exemple Holding Group" in html
    assert "Geneve, Suisse" in html
    assert "2.5 Mrd €" in html  # revenue = 2.5 billion
    assert "750.0 M€" in html  # market_cap = 750 million

    # Business activities, mission, core values
    assert "Paiements en ligne" in html
    assert "Rendre la finance accessible a tous." in html
    assert "Integrite" in html

    # History: founding story, milestones, acquisitions (dict + string branches)
    assert "L'entreprise a ete fondee par trois ingenieurs en 1998." in html
    assert "1998: Fondation a Geneve" in html
    assert "cible: FinTech Absorbee" in html

    # Financials: trends table (including N/A for None profit), ratios, debt, investors
    assert "300000000" in html
    assert "N/A" in html
    assert "Marge Nette" in html
    assert "12%" in html
    assert "Dette Court Terme" in html
    assert "100M€" in html
    assert "Fonds Alpha Capital" in html

    # Market position: share, landscape, competitors, advantages, opportunities, challenges
    assert "18% du marche europeen" in html
    assert "Marche fragmente avec 5 acteurs majeurs." in html
    assert "Concurrent Un" in html
    assert "Technologie proprietaire brevetee" in html
    assert "Expansion en Asie du Sud-Est" in html
    assert "Pression reglementaire croissante" in html

    # Products and services
    assert "Exemple Pay" in html
    assert "Exemple Pay Business" in html
    assert "Modele freemium avec abonnement premium" in html
    assert "PME" in html

    # Management: executives with name/role, nom/titre, and position-only fallback
    assert "Alice Dupont-Exemple" in html
    assert "Directrice Generale" in html
    assert "Bernard Martin-Exemple" in html
    assert "Directeur Financier" in html
    assert "Fallback Position Only" in html
    assert "Membre Conseil Un" in html
    assert "Culture d'innovation et de transparence radicale" in html

    # Legal compliance
    assert "Regule par la FINMA en Suisse" in html
    assert "Audit reussi en 2022" in html
    assert "Litige en cours avec ExPartner Corp" in html

    # Raw JSON debug section marker
    assert "Voir les données brutes" in html


def test_company_profiler_empty_optional_sections_render_without_raising():
    """All optional sections empty: renderer should skip them, not raise."""
    data = {
        "company_name": "Minimal Co",
        "core_info": {},
        "history": {},
        "financials": {},
        "market_position": {},
        "products_and_services": {},
        "management": {},
        "legal_compliance": {},
    }

    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "<!DOCTYPE html>" in html
    assert "Minimal Co" in html
    # None of the section headers should have been added since every section is empty
    assert "Informations Clés" not in html
    assert "Histoire de l'Entreprise" not in html
    assert "Analyse Financière" not in html
    assert "Position sur le Marché" not in html
    assert "Produits et Services" not in html
    assert "Direction et Gouvernance" not in html
    assert "Conformité Légale" not in html
    # Raw data section is always present
    assert "Voir les données brutes" in html


def test_company_profiler_completely_empty_dict_uses_default_company_name():
    """No keys at all: header falls back to the default company name."""
    html = TemplateManager().render_report(CREW_IDENTIFIER, {})

    assert "<!DOCTYPE html>" in html
    assert "Entreprise" in html
    assert "Profil d'Entreprise" in html


def test_company_profiler_acquisition_as_plain_string():
    """acquisitions_and_mergers items may be plain strings, not just dicts.

    The Pydantic model requires dict items here, so this exercises the
    renderer's ``else`` branch directly via a plain dict payload.
    """
    data = {
        "company_name": "String Acquisition Co",
        "history": {
            "acquisitions_and_mergers": ["Fusion informelle avec PartnerCo"],
        },
    }

    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "Fusion informelle avec PartnerCo" in html
    assert "Acquisitions et fusions" in html


def test_company_profiler_debt_structure_as_plain_string():
    """debt_structure may be a free-text string instead of a dict."""
    data = {
        "company_name": "Debt String Co",
        "financials": {"debt_structure": "Aucune dette a long terme, dette a court terme minime."},
    }

    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "Aucune dette a long terme, dette a court terme minime." in html
    assert "Structure de la dette" in html


def test_company_profiler_currency_formatting_branches():
    """Directly exercise every branch of the currency formatting helper."""
    fmt = CompanyProfilerRenderer._format_currency

    assert fmt(None) is None
    assert fmt(3_200_000_000) == "3.2 Mrd €"
    assert fmt(750_000_000) == "750.0 M€"
    assert fmt(5_000) == "5.0 k€"
    assert fmt(750) == "750 €"


def test_company_profiler_small_revenue_renders_kilo_and_unit_euro_branches():
    """core_info revenue/market_cap small values hit k€ and plain € branches."""
    data = {
        "company_name": "Small Revenue Co",
        "core_info": {
            "legal_name": "Small Revenue Co SARL",
            "revenue": 5_000,  # -> "5.0 k€"
            "market_cap": 750,  # -> "750 €"
        },
    }

    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "5.0 k€" in html
    assert "750 €" in html


def test_company_profiler_single_executive_without_name_or_role():
    """Executive dict missing every known key falls back to 'N/A' name and no role tag."""
    data = {
        "company_name": "No Names Co",
        "management": {
            "key_executives": [{"unrelated_field": "value"}],
        },
    }

    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "Direction et Gouvernance" in html
    assert "N/A" in html
