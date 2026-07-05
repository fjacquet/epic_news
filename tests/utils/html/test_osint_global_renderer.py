"""Tests for the OSINT Global HTML renderer.

Renders through the public path (``TemplateManager.render_report``) using the
``OSINT_GLOBAL`` crew identifier registered in ``RendererFactory``. This
renderer combines up to seven sub-reports (company profile, tech stack, web
presence, HR intelligence, legal analysis, geospatial analysis and cross
reference) produced by ``ReceptionFlow._generate_osint_consolidated_report``
(see ``src/epic_news/main.py``), which is the exact shape mirrored here.
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
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.models.crews.geospatial_analysis_report import GeospatialAnalysisReport
from epic_news.models.crews.hr_intelligence_report import HRIntelligenceReport
from epic_news.models.crews.legal_analysis_report import LegalAnalysisReport
from epic_news.models.crews.tech_stack_report import TechStackComponent, TechStackReport
from epic_news.models.crews.web_presence_report import (
    CompetitiveAnalysis,
    DataLeak,
    SocialMediaPresence,
    TechnicalInfrastructure,
    WebPresenceReport,
    WebsiteAnalysis,
)
from epic_news.utils.html.template_manager import TemplateManager

CREW_IDENTIFIER = "OSINT_GLOBAL"

# All section ids the renderer can emit, keyed by their source data field.
_SECTION_IDS = {
    "company_profile": "company-profile",
    "tech_stack": "tech-stack",
    "web_presence": "web-presence",
    "hr_intelligence": "hr-intelligence",
    "legal_analysis": "legal-analysis",
    "geospatial_analysis": "geospatial",
    "cross_reference": "cross-reference",
}


def _build_company_profile(marker: str) -> dict:
    return CompanyProfileReport(
        company_name=marker,
        core_info=CompanyCoreInfo(
            legal_name=f"{marker} SA",
            year_founded=1999,
            headquarters_location="Geneva, Switzerland",
            industry_classification="Enterprise Software",
            business_activities=["SaaS", "Consulting"],
            corporate_structure="Private limited company",
            ownership_details="Founder-owned, no external investors",
        ),
        history=CompanyHistory(
            key_milestones=["Founded in 1999", "IPO in 2010"],
            founding_story="Started in a garage in Geneva.",
        ),
        financials=Financials(
            revenue_and_profit_trends=[{"year": 2023, "revenue": 1_000_000}],
            key_financial_ratios={"debt_to_equity": 0.5},
        ),
        market_position=MarketPosition(
            competitive_landscape="Highly competitive SaaS market",
            key_competitors=["CompetitorA", "CompetitorB"],
            comparative_advantages=["Strong brand recognition"],
            industry_trends=["AI adoption"],
            growth_opportunities=["Expansion in APAC"],
            challenges=["Regulatory pressure"],
        ),
        products_and_services=ProductsAndServices(
            core_product_lines=["Product Alpha", "Product Beta"],
            customer_segments=["Enterprise", "SMB"],
        ),
        management=Management(
            key_executives=[{"name": "Jane Doe", "role": "CEO"}],
            board_of_directors=["John Smith"],
            corporate_culture="Innovative and open",
        ),
        legal_compliance=LegalCompliance(
            regulatory_framework="GDPR compliant",
            compliance_history=["No major violations reported"],
        ),
    ).model_dump()


def _build_tech_stack(marker: str) -> dict:
    return TechStackReport(
        company_name=marker,
        executive_summary=f"{marker} runs on a modern, cloud-native stack.",
        technology_stack=[TechStackComponent(name="Python", category="Language")],
        strengths=["Modern stack"],
        weaknesses=["Legacy billing system"],
        open_source_contributions=["acme-toolkit"],
        talent_assessment="Strong engineering team with senior hires",
        recommendations=["Adopt Kubernetes for orchestration"],
    ).model_dump()


def _build_web_presence(marker: str) -> dict:
    return WebPresenceReport(
        company_name=marker,
        executive_summary=f"{marker} has a solid but improvable web presence.",
        website_analysis=WebsiteAnalysis(
            domain="acme.example.com",
            structure="Clear navigation with main menu",
            content_quality="Rich, regularly updated content",
            seo="Good overall SEO score of 85/100",
            recommendations=["Improve mobile load time"],
        ),
        social_media_footprint=[
            SocialMediaPresence(
                platform="LinkedIn",
                url="https://linkedin.com/company/acme",
                followers=15234,
                engagement_rate=0.042,
                notes="Regular B2B engagement",
            )
        ],
        technical_infrastructure=TechnicalInfrastructure(hosting_provider="AWS"),
        data_leak_analysis=[
            DataLeak(
                source="HaveIBeenPwned",
                date="2025-03-14",
                description="Employee email leak detected on a third-party forum",
                risk_level="High",
            )
        ],
        competitive_analysis=[
            CompetitiveAnalysis(
                competitor_name="Beta Industries",
                website="https://beta-industries.example.com",
                strengths=["Better local SEO"],
                weaknesses=["Slow website"],
            )
        ],
    ).model_dump()


def _build_hr_intelligence(marker: str) -> dict:
    return HRIntelligenceReport(
        company_name=marker,
        leadership_assessment={"summary": "Strong, stable leadership team"},
        employee_sentiment={"score": 4.2},
        organizational_culture={"style": "Flat hierarchy"},
        talent_acquisition_strategy={"approach": "Employer branding first"},
        summary_and_recommendations=f"{marker} HR-INTEL-MARKER recommendations.",
    ).model_dump()


def _build_legal_analysis(marker: str) -> dict:
    return LegalAnalysisReport(
        company_name=marker,
        compliance_assessment={"status": "Compliant"},
        ip_portfolio_analysis={"patents": 12},
        regulatory_risk_assessment={"risk": "Low"},
        litigation_history=[{"case": "LEGAL-MARKER dispute", "status": "Settled"}],
        ma_due_diligence={"summary": "Clean due diligence"},
    ).model_dump()


def _build_geospatial_analysis(marker: str) -> dict:
    return GeospatialAnalysisReport(
        company_name=marker,
        physical_locations=[{"city": "Geneva", "country": "Switzerland"}],
        risk_assessment=[{"region": "EU", "risk": "GEOSPATIAL-MARKER-low"}],
        supply_chain_map=[{"node": "Supplier A", "location": "China"}],
        mergers_and_acquisitions_insights=[{"target": "StartupX", "location": "Berlin"}],
    ).model_dump()


def _build_cross_reference(marker: str) -> dict:
    return CrossReferenceReport(
        target=marker,
        executive_summary=f"{marker} CROSS-REFERENCE-MARKER summary.",
        detailed_findings={"key_finding": "Consolidated intelligence points to strong growth."},
        confidence_assessment="High confidence",
        information_gaps=["Missing detailed financial breakdown"],
    ).model_dump()


def _full_osint_dict(company_name: str = "Acme Global Corp") -> dict:
    """Build a fully populated OSINT global dict mirroring main.py's shape."""
    return {
        "company_name": company_name,
        "company_profile": _build_company_profile(company_name),
        "tech_stack": _build_tech_stack(company_name),
        "web_presence": _build_web_presence(company_name),
        "hr_intelligence": _build_hr_intelligence(company_name),
        "legal_analysis": _build_legal_analysis(company_name),
        "geospatial_analysis": _build_geospatial_analysis(company_name),
        "cross_reference": _build_cross_reference(company_name),
    }


def test_osint_global_full_data_renders_all_sections():
    """Full data: every sub-report section should render with fed-in content."""
    data = _full_osint_dict("Acme Global Corp")
    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    # Structural markers
    assert "<!DOCTYPE html>" in html
    assert 'class="osint-global-report"' in html
    assert "Rapport OSINT Complet" in html

    # Header + executive summary use the company name
    assert "Acme Global Corp" in html
    assert "Entreprise:" in html
    assert "Rapports disponibles:" in html
    assert "7 sur 7" in html

    # Every section id is present with its title
    for section_id in [
        "executive-summary",
        "company-profile",
        "tech-stack",
        "web-presence",
        "hr-intelligence",
        "legal-analysis",
        "geospatial",
        "cross-reference",
    ]:
        assert f'id="{section_id}"' in html

    # Table of contents links to every section, EXCEPT "geospatial": see the
    # KNOWN BUG note below -- reused verbatim in the partial-data test.
    for section_id in _SECTION_IDS.values():
        if section_id == "geospatial":
            continue
        assert f'href="#{section_id}"' in html
    assert 'href="#executive-summary"' in html

    # KNOWN BUG (pre-existing, not fixed here): _add_table_of_contents derives
    # data_key = section_id.replace("-", "_"), so for section_id="geospatial"
    # it looks up data.get("geospatial") -- but the actual data key is
    # "geospatial_analysis". The TOC link to #geospatial is therefore NEVER
    # added, even though the "geospatial" *section itself* (added separately
    # via _add_geospatial_section) renders fine below.
    assert 'href="#geospatial"' not in html

    # Back-to-top links: one per sub-report section (7)
    assert html.count("Retour au sommaire") == 7

    # Raw JSON debug blocks exist per sub-report, with their own title
    assert "Donnees brutes - Profil de l'Entreprise" in html
    assert "Donnees brutes - Rapport de Synthese" in html

    # Content markers fed into each sub-report round-trip through either the
    # sub-renderer's own formatting or (at minimum) the raw JSON dump.
    assert "HR-INTEL-MARKER" in html
    assert "LEGAL-MARKER" in html
    assert "GEOSPATIAL-MARKER" in html
    assert "CROSS-REFERENCE-MARKER" in html
    assert "Consolidated intelligence points to strong growth." in html


def test_osint_global_minimal_data_only_company_name():
    """Minimal data (company name only): no crash, no optional sections."""
    data = {"company_name": "Solo Corp"}
    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "<!DOCTYPE html>" in html
    assert "Solo Corp" in html
    assert "Rapports disponibles:" in html
    assert "0 sur 7" in html

    # No sub-report section should be rendered
    for section_id in _SECTION_IDS.values():
        assert f'id="{section_id}"' not in html
        assert f'href="#{section_id}"' not in html

    # Only the always-present executive summary anchor exists in the TOC
    assert 'href="#executive-summary"' in html
    assert "Retour au sommaire" not in html


def test_osint_global_empty_data_no_company_name():
    """Fully empty dict: header/summary omit the optional company line."""
    html = TemplateManager().render_report(CREW_IDENTIFIER, {})

    assert "<!DOCTYPE html>" in html
    assert "Rapport OSINT Complet" in html
    assert "Rapports disponibles:" in html
    assert "0 sur 7" in html

    # The "Entreprise: ..." line is only added when company_name is present
    assert "Entreprise:" not in html

    for section_id in _SECTION_IDS.values():
        assert f'id="{section_id}"' not in html


def test_osint_global_partial_data_mixes_present_and_absent_sections():
    """Partial data: only some sub-reports present -> selective TOC/sections."""
    company_name = "Partial Corp"
    data = {
        "company_name": company_name,
        "company_profile": _build_company_profile(company_name),
        "geospatial_analysis": _build_geospatial_analysis(company_name),
    }
    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "2 sur 7" in html

    # Present sections
    assert 'id="company-profile"' in html
    assert 'id="geospatial"' in html
    assert 'href="#company-profile"' in html
    # KNOWN BUG (see full-data test): the TOC never links to "#geospatial"
    # because of a data-key mismatch in _add_table_of_contents, even though
    # the geospatial section itself is rendered (asserted above).
    assert 'href="#geospatial"' not in html

    # Absent sections
    for missing_id in ["tech-stack", "web-presence", "hr-intelligence", "legal-analysis", "cross-reference"]:
        assert f'id="{missing_id}"' not in html
        assert f'href="#{missing_id}"' not in html

    # Exactly the two present sub-reports contribute a back-to-top link
    assert html.count("Retour au sommaire") == 2


def test_osint_global_sub_renderer_exception_is_caught_and_reported():
    """A sub-report shaped incompatibly with its renderer must not crash the
    whole OSINT report: ``_add_sub_report_section`` catches the exception and
    renders an error paragraph instead, while the raw JSON block still shows
    the offending payload.

    NOTE: this exercises a real, reachable failure mode -- ``company_profile``
    is expected to be a dict (see ``CompanyProfileReport``), and
    ``CompanyProfilerRenderer._add_header`` unconditionally calls
    ``data.get(...)``. If it's fed a non-dict value (e.g. malformed upstream
    JSON), that raises ``AttributeError`` deep in the sub-renderer, which this
    test confirms is swallowed gracefully by the global renderer.
    """
    data = {
        "company_name": "Broken Co",
        "company_profile": "not-a-dict-payload",
    }
    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "<!DOCTYPE html>" in html
    assert 'id="company-profile"' in html
    assert "Erreur lors du rendu de la section Profil de l'Entreprise" in html
    # The raw (invalid) payload is still dumped for debugging purposes
    assert "not-a-dict-payload" in html
