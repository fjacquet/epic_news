"""Tests for the Tech Stack HTML renderer.

Renders through the public path (``TemplateManager.render_report``) using the
``TECH_STACK`` crew identifier registered in ``RendererFactory``.
"""

from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.utils.html.template_manager import TemplateManager


def _full_report_dict() -> dict:
    """Build a fully-populated, valid TechStackReport as a dict."""
    return TechStackReport(
        company_name="Acme Corp",
        executive_summary="Acme Corp mise sur une stack moderne mais avec de la dette technique.",
        technology_stack=[
            {"name": "Python", "category": "Backend", "description": "Langage principal du backend"},
            {"name": "FastAPI", "category": "Backend", "description": "Framework API REST"},
            {"name": "React", "category": "Frontend", "description": "Bibliothèque UI"},
            {"name": "PostgreSQL", "category": "Database"},
        ],
        strengths=["Équipe expérimentée", "CI/CD mature"],
        weaknesses=["Peu de tests automatisés", "Documentation éparse"],
        open_source_contributions=["Contribue à Apache Airflow", "Maintient une lib interne publiée"],
        talent_assessment="L'équipe technique est senior mais en sous-effectif sur le DevOps.",
        recommendations=["Renforcer l'équipe DevOps", "Investir dans les tests automatisés"],
    ).model_dump()


def test_tech_stack_full_data_renders_all_sections():
    """Full data: every section should render with the exact content fed in."""
    data = _full_report_dict()
    html = TemplateManager().render_report("TECH_STACK", data)

    # Structural markers
    assert "<!DOCTYPE html>" in html
    assert 'class="tech-stack-report"' in html
    assert 'class="report-header"' in html

    # Header
    assert "Analyse de la Stack Technologique" in html
    assert "Acme Corp" in html

    # Executive summary
    assert "Résumé Exécutif" in html
    assert "Acme Corp mise sur une stack moderne mais avec de la dette technique." in html

    # Technology stack section, grouped by category
    assert "Technologies Utilisées" in html
    assert 'class="tech-category"' in html
    assert 'class="tech-grid"' in html
    assert 'class="tech-card"' in html
    assert "Backend" in html
    assert "Frontend" in html
    assert "Database" in html
    assert "Python" in html
    assert "Langage principal du backend" in html
    assert "FastAPI" in html
    assert "Framework API REST" in html
    assert "React" in html
    assert "Bibliothèque UI" in html
    assert "PostgreSQL" in html

    # Strengths & weaknesses (SWOT grid)
    assert "Forces et Faiblesses" in html
    assert 'class="swot-grid"' in html
    assert 'class="strengths-card"' in html
    assert 'class="weaknesses-card"' in html
    assert "✅ Forces" in html
    assert "Équipe expérimentée" in html
    assert "CI/CD mature" in html
    assert "⚠️ Faiblesses" in html
    assert "Peu de tests automatisés" in html
    assert "Documentation éparse" in html

    # Open source contributions
    assert "Contributions Open Source" in html
    assert "Contribue à Apache Airflow" in html
    assert "Maintient une lib interne publiée" in html

    # Talent assessment
    assert "Évaluation des Talents" in html
    assert "L'équipe technique est senior mais en sous-effectif sur le DevOps." in html

    # Recommendations
    assert "Recommandations" in html
    assert 'class="recommendations-list"' in html
    assert "Renforcer l'équipe DevOps" in html
    assert "Investir dans les tests automatisés" in html

    # Raw JSON debug section present
    assert "Voir les données brutes" in html
    assert "Acme Corp" in html  # appears again inside <pre><code> JSON dump


def test_tech_stack_minimal_data_does_not_crash_and_omits_optional_sections():
    """Minimal/empty optional fields: renderer must not crash and must skip sections."""
    data = {
        "company_name": "Minimal Inc",
        "executive_summary": None,
        "technology_stack": [],
        "strengths": [],
        "weaknesses": [],
        "open_source_contributions": [],
        "talent_assessment": None,
        "recommendations": [],
    }

    html = TemplateManager().render_report("TECH_STACK", data)

    assert "<!DOCTYPE html>" in html
    assert 'class="tech-stack-report"' in html
    assert "Minimal Inc" in html

    # Optional sections must be entirely absent since their inputs are falsy
    assert "Résumé Exécutif" not in html
    assert "Technologies Utilisées" not in html
    assert "Forces et Faiblesses" not in html
    assert "Contributions Open Source" not in html
    assert "Évaluation des Talents" not in html
    assert "Recommandations" not in html

    # The report is still a substantial, valid HTML document (header + raw JSON)
    assert len(html) > 500
    assert "Voir les données brutes" in html


def test_tech_stack_only_strengths_no_weaknesses():
    """SWOT grid renders the strengths card alone when weaknesses is empty."""
    data = _full_report_dict()
    data["weaknesses"] = []
    data["technology_stack"] = []
    data["open_source_contributions"] = []
    data["recommendations"] = []

    html = TemplateManager().render_report("TECH_STACK", data)

    assert "Forces et Faiblesses" in html
    assert "✅ Forces" in html
    assert "Équipe expérimentée" in html
    assert "⚠️ Faiblesses" not in html


def test_tech_stack_only_weaknesses_no_strengths():
    """SWOT grid renders the weaknesses card alone when strengths is empty."""
    data = _full_report_dict()
    data["strengths"] = []
    data["technology_stack"] = []
    data["open_source_contributions"] = []
    data["recommendations"] = []

    html = TemplateManager().render_report("TECH_STACK", data)

    assert "Forces et Faiblesses" in html
    assert "⚠️ Faiblesses" in html
    assert "Peu de tests automatisés" in html
    assert "✅ Forces" not in html


def test_tech_stack_technology_without_description_and_default_category():
    """A tech entry with no description omits the <p>, and missing category falls back to 'Autre'."""
    data = _full_report_dict()
    data["technology_stack"] = [{"name": "Redis"}]
    data["strengths"] = []
    data["weaknesses"] = []
    data["open_source_contributions"] = []
    data["recommendations"] = []

    html = TemplateManager().render_report("TECH_STACK", data)

    assert "Technologies Utilisées" in html
    assert "Autre" in html
    assert "Redis" in html


def test_tech_stack_technology_missing_name_defaults_to_na():
    """A tech entry missing 'name' falls back to 'N/A' for the card title."""
    data = _full_report_dict()
    data["technology_stack"] = [{"category": "Infra", "description": "Sans nom"}]
    data["strengths"] = []
    data["weaknesses"] = []
    data["open_source_contributions"] = []
    data["recommendations"] = []

    html = TemplateManager().render_report("TECH_STACK", data)

    assert "<h4>N/A</h4>" in html
    assert "Sans nom" in html
