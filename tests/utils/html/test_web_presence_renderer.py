"""Tests for the Web Presence HTML renderer.

Renders through the public path (``TemplateManager.render_report``) using the
``WEB_PRESENCE`` crew identifier registered in ``RendererFactory``.
"""

from epic_news.models.crews.web_presence_report import WebPresenceReport
from epic_news.utils.html.template_manager import TemplateManager


def _full_report_dict() -> dict:
    """Build a fully-populated, valid WebPresenceReport as a dict."""
    return WebPresenceReport(
        company_name="Acme Corp",
        executive_summary="Acme Corp a une présence web solide mais perfectible.",
        website_analysis={
            "domain": "acme.example.com",
            "structure": "Navigation claire avec menu principal",
            "content_quality": "Contenu riche et régulièrement mis à jour",
            "seo": "Bon score SEO global de 85/100",
            "recommendations": [
                "Améliorer le temps de chargement mobile",
                "Ajouter des données structurées Schema.org",
            ],
        },
        social_media_footprint=[
            {
                "platform": "LinkedIn",
                "url": "https://linkedin.com/company/acme",
                "followers": 15234,
                "engagement_rate": 0.042,
                "notes": "Publications régulières, forte interaction B2B",
            },
            {
                "platform": "Twitter",
                "url": "https://twitter.com/acme",
                "followers": 8900,
                "engagement_rate": 0.021,
                "notes": "Activité modérée",
            },
        ],
        technical_infrastructure={
            "hosting_provider": "AWS",
            "dns_provider": "Cloudflare",
            "cdn_provider": "Cloudflare CDN",
            "ssl_issuer": "Let's Encrypt",
        },
        data_leak_analysis=[
            {
                "source": "HaveIBeenPwned",
                "date": "2025-03-14",
                "description": "Fuite d'emails employés détectée sur un forum tiers",
                "risk_level": "High",
            },
            {
                "source": "Dark Web Monitor",
                "date": "2024-11-02",
                "description": "Mention de credentials internes obsolètes",
                "risk_level": "Low",
            },
        ],
        competitive_analysis=[
            {
                "competitor_name": "Beta Industries",
                "website": "https://beta-industries.example.com",
                "strengths": ["Meilleur SEO local", "Forte présence Instagram"],
                "weaknesses": ["Site lent", "Peu de contenu technique"],
            },
        ],
    ).model_dump()


def test_web_presence_full_data_renders_all_sections():
    """Full data: every section should render with the exact content fed in."""
    data = _full_report_dict()
    html = TemplateManager().render_report("WEB_PRESENCE", data)

    # Structural markers
    assert "<!DOCTYPE html>" in html
    assert 'class="web-presence-report"' in html
    assert 'class="report-header"' in html

    # Header
    assert "Analyse de Présence Web" in html
    assert "Acme Corp" in html

    # Executive summary
    assert "Acme Corp a une présence web solide mais perfectible." in html

    # Website analysis section
    assert "Analyse du Site Web" in html
    assert "Domaine: acme.example.com" in html
    assert "Navigation claire avec menu principal" in html
    assert "Contenu riche et régulièrement mis à jour" in html
    assert "Bon score SEO global de 85/100" in html
    assert "Améliorer le temps de chargement mobile" in html
    assert "Ajouter des données structurées Schema.org" in html

    # Social media footprint section (multi-item list)
    assert "Empreinte Réseaux Sociaux" in html
    assert "LinkedIn" in html
    assert "https://linkedin.com/company/acme" in html
    assert "15,234 abonnés" in html
    assert "4.2% engagement" in html
    assert "Publications régulières, forte interaction B2B" in html
    assert "Twitter" in html
    assert "8,900 abonnés" in html

    # Technical infrastructure section (table)
    assert "Infrastructure Technique" in html
    assert "Hébergeur" in html
    assert "AWS" in html
    assert "Fournisseur DNS" in html
    assert "Cloudflare" in html
    assert "CDN" in html
    assert "Cloudflare CDN" in html
    assert "Émetteur SSL" in html
    assert "Let's Encrypt" in html

    # Data leak analysis section (multi-item, risk levels drive CSS classes)
    assert "Analyse des Fuites de Données" in html
    assert "HaveIBeenPwned" in html
    assert "2025-03-14" in html
    assert "Fuite d'emails employés détectée sur un forum tiers" in html
    assert "Risque: High" in html
    assert 'class="leak-card risk-high"' in html
    assert "Dark Web Monitor" in html
    assert "Risque: Low" in html
    assert 'class="leak-card risk-low"' in html

    # Competitive analysis section
    assert "Analyse Concurrentielle" in html
    assert "Beta Industries" in html
    assert "https://beta-industries.example.com" in html
    assert "Meilleur SEO local" in html
    assert "Forte présence Instagram" in html
    assert "Site lent" in html
    assert "Peu de contenu technique" in html

    # Raw JSON debug section present
    assert "Voir les données brutes" in html
    assert "Acme Corp" in html  # appears again inside <pre><code> JSON dump


def test_web_presence_minimal_data_does_not_crash_and_omits_optional_sections():
    """Minimal/empty optional fields: renderer must not crash and must skip sections."""
    data = {
        "company_name": "Minimal Inc",
        "executive_summary": None,
        "website_analysis": None,
        "social_media_footprint": [],
        "technical_infrastructure": None,
        "data_leak_analysis": [],
        "competitive_analysis": [],
    }

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "<!DOCTYPE html>" in html
    assert 'class="web-presence-report"' in html
    assert "Minimal Inc" in html

    # Optional sections must be entirely absent since their inputs are falsy
    assert "Résumé Exécutif" not in html
    assert "Analyse du Site Web" not in html
    assert "Empreinte Réseaux Sociaux" not in html
    assert "Infrastructure Technique" not in html
    assert "Analyse des Fuites de Données" not in html
    assert "Analyse Concurrentielle" not in html

    # The report is still a substantial, valid HTML document (header + raw JSON)
    assert len(html) > 500
    assert "Voir les données brutes" in html


def test_web_presence_website_analysis_partial_fields_and_no_recommendations():
    """Website analysis with some falsy fields and an empty recommendations list."""
    data = _full_report_dict()
    data["website_analysis"] = {
        "domain": "",  # falsy -> "Domaine:" line omitted
        "structure": "Structure basique",
        "content_quality": "",  # falsy -> omitted
        "seo": "SEO non optimisé",
        "recommendations": [],  # falsy -> recommendations block omitted
    }
    data["social_media_footprint"] = []
    data["technical_infrastructure"] = None
    data["data_leak_analysis"] = []
    data["competitive_analysis"] = []

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "Analyse du Site Web" in html
    assert "Domaine:" not in html
    assert "Structure basique" in html
    assert "SEO non optimisé" in html
    assert "Recommandations" not in html

    # Sibling sections skipped
    assert "Empreinte Réseaux Sociaux" not in html
    assert "Infrastructure Technique" not in html
    assert "Analyse des Fuites de Données" not in html
    assert "Analyse Concurrentielle" not in html


def test_web_presence_social_media_card_without_optional_fields():
    """Social media card branch: no url, no followers, no engagement, no notes."""
    data = _full_report_dict()
    data["social_media_footprint"] = [
        {"platform": "Mastodon"},
    ]
    data["website_analysis"] = None
    data["technical_infrastructure"] = None
    data["data_leak_analysis"] = []
    data["competitive_analysis"] = []

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "Empreinte Réseaux Sociaux" in html
    assert "Mastodon" in html
    # No followers/engagement/notes/url provided, so none of those markers appear
    assert "abonnés" not in html
    assert "engagement" not in html


def test_web_presence_social_media_platform_defaults_to_na():
    """Social media entry missing 'platform' key falls back to 'N/A'."""
    data = _full_report_dict()
    data["social_media_footprint"] = [{"url": "https://example.com/profile"}]
    data["website_analysis"] = None
    data["technical_infrastructure"] = None
    data["data_leak_analysis"] = []
    data["competitive_analysis"] = []

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "<h3>N/A</h3>" in html
    assert "https://example.com/profile" in html


def test_web_presence_technical_infrastructure_partial_fields():
    """Only some technical infrastructure fields populated -> only those rows render."""
    data = _full_report_dict()
    data["technical_infrastructure"] = {
        "hosting_provider": "OVH",
        "dns_provider": None,
        "cdn_provider": None,
        "ssl_issuer": None,
    }
    data["website_analysis"] = None
    data["social_media_footprint"] = []
    data["data_leak_analysis"] = []
    data["competitive_analysis"] = []

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "Infrastructure Technique" in html
    assert "Hébergeur" in html
    assert "OVH" in html
    assert "Fournisseur DNS" not in html
    assert "CDN" not in html
    assert "Émetteur SSL" not in html


def test_web_presence_data_leak_unknown_risk_level_defaults():
    """Data leak entry missing risk_level/source/date/description falls back gracefully."""
    data = _full_report_dict()
    data["data_leak_analysis"] = [{}]
    data["website_analysis"] = None
    data["social_media_footprint"] = []
    data["technical_infrastructure"] = None
    data["competitive_analysis"] = []

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "Analyse des Fuites de Données" in html
    assert 'class="leak-card risk-unknown"' in html
    assert "Risque: N/A" in html


def test_web_presence_competitor_without_website_or_strengths_weaknesses():
    """Competitor card with only the required name field."""
    data = _full_report_dict()
    data["competitive_analysis"] = [{"competitor_name": "Gamma Ltd"}]
    data["website_analysis"] = None
    data["social_media_footprint"] = []
    data["technical_infrastructure"] = None
    data["data_leak_analysis"] = []

    html = TemplateManager().render_report("WEB_PRESENCE", data)

    assert "Analyse Concurrentielle" in html
    assert "Gamma Ltd" in html
    assert "✅ Forces" not in html
    assert "⚠️ Faiblesses" not in html
