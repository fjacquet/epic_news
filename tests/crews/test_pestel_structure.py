"""Structural tests for the PESTEL crew and its rendering helper."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from epic_news.crews.pestel.pestel_crew import PestelCrew
from epic_news.models.content_state import CrewCategories
from epic_news.models.crews.pestel_report import PestelDimension, PestelReport
from epic_news.utils.html.template_renderers.pestel_markdown import pestel_to_markdown
from epic_news.utils.html.template_renderers.pestel_renderer import PestelRenderer
from epic_news.utils.html.template_renderers.renderer_factory import RendererFactory


@pytest.fixture
def sample_report() -> PestelReport:
    dim = PestelDimension(
        summary="Summary",
        key_factors=["f1", "f2"],
        impact_analysis="Impact",
        sources=["https://example.com"],
    )
    return PestelReport(
        topic="Test Topic",
        executive_summary="Exec summary",
        political=dim,
        economic=dim,
        social=dim,
        technological=dim,
        environmental=dim,
        legal=dim,
        synthesis="Cross-dim synthesis",
        generated_at="2026-04-24",
    )


def test_pestel_report_instantiation(sample_report: PestelReport) -> None:
    assert sample_report.topic == "Test Topic"
    assert sample_report.political.key_factors == ["f1", "f2"]
    assert sample_report.synthesis == "Cross-dim synthesis"


def test_pestel_report_requires_all_dimensions() -> None:
    """Every PESTEL dimension must be supplied — no silent defaults."""
    dim = PestelDimension(summary="s", impact_analysis="i")
    with pytest.raises(ValidationError):
        PestelReport(  # type: ignore[call-arg]
            topic="T",
            executive_summary="E",
            political=dim,
            # missing economic, social, technological, environmental, legal
            synthesis="S",
            generated_at="2026-04-24",
        )


def test_pestel_dimension_defaults_empty_lists() -> None:
    dim = PestelDimension(summary="s", impact_analysis="i")
    assert dim.key_factors == []
    assert dim.sources == []


def test_pestel_to_markdown_contains_all_sections(sample_report: PestelReport) -> None:
    md = pestel_to_markdown(sample_report)
    assert "# PESTEL Analysis — Test Topic" in md
    for heading in (
        "🏛️ Political",
        "💰 Economic",
        "👥 Social",
        "💻 Technological",
        "🌍 Environmental",
        "⚖️ Legal",
        "🎯 Synthesis",
    ):
        assert heading in md
    assert "- https://example.com" in md.splitlines()
    assert "Cross-dim synthesis" in md


def test_pestel_category_registered() -> None:
    assert CrewCategories.PESTEL == "PESTEL"
    assert CrewCategories.to_dict().get("PESTEL") == "PESTEL"


def test_pestel_markdown_handles_empty_factors_and_sources() -> None:
    """Empty key_factors → '_(none identified)_'; empty sources → no Sources section."""
    dim = PestelDimension(summary="s", impact_analysis="i")  # both lists default empty
    report = PestelReport(
        topic="Empty Topic",
        executive_summary="exec",
        political=dim,
        economic=dim,
        social=dim,
        technological=dim,
        environmental=dim,
        legal=dim,
        synthesis="syn",
        generated_at="2026-04-25",
    )
    md = pestel_to_markdown(report)
    assert "_(none identified)_" in md
    assert "**Sources**" not in md  # section omitted when no sources


def test_pestel_markdown_preserves_french_and_unicode_characters() -> None:
    dim = PestelDimension(
        summary="L'économie française évolue — voilà",
        key_factors=["taux d'intérêt", "inflation €"],
        impact_analysis="Réglementation stricte",
        sources=["https://example.fr/réf"],
    )
    report = PestelReport(
        topic="Société Générale",
        executive_summary="Résumé exécutif",
        political=dim,
        economic=dim,
        social=dim,
        technological=dim,
        environmental=dim,
        legal=dim,
        synthesis="Synthèse cross-dimensionnelle",
        generated_at="2026-04-25",
    )
    md = pestel_to_markdown(report)
    assert "Société Générale" in md
    assert "L'économie française évolue" in md
    assert "taux d'intérêt" in md
    assert "https://example.fr/réf" in md
    assert "Synthèse cross-dimensionnelle" in md


def test_pestel_yaml_configs_parse_cleanly() -> None:
    """agents.yaml and tasks.yaml under crews/pestel/config/ must be valid YAML."""
    config_dir = Path(__file__).resolve().parents[2] / "src" / "epic_news" / "crews" / "pestel" / "config"
    agents = yaml.safe_load((config_dir / "agents.yaml").read_text(encoding="utf-8"))
    tasks = yaml.safe_load((config_dir / "tasks.yaml").read_text(encoding="utf-8"))

    assert "political_researcher" in agents
    assert "pestel_reporter" in agents
    assert "format_pestel_report_task" in tasks
    # Each researcher task references current_date in its description
    assert "current_date" in tasks["political_research_task"]["description"]


def test_pestel_html_renderer_registered() -> None:
    """PESTEL must resolve to a specialized HTML renderer (not GenericRenderer)."""
    assert RendererFactory.has_specialized_renderer("PESTEL")
    renderer = RendererFactory.create_renderer("PESTEL")
    assert isinstance(renderer, PestelRenderer)


def test_pestel_renderer_emits_all_sections(sample_report: PestelReport) -> None:
    """The HTML output must include the topic, all six dimension headings, and sources."""
    html = PestelRenderer().render(sample_report.model_dump())
    assert "Test Topic" in html
    for heading in ("Political", "Economic", "Social", "Technological", "Environmental", "Legal"):
        assert heading in html
    assert "Synthesis" in html
    assert "Cross-dim synthesis" in html
    # URL sources rendered as anchor tags
    assert 'href="https://example.com"' in html


def test_pestel_renderer_handles_empty_lists() -> None:
    """Empty key_factors → empty-state paragraph; empty sources → no Sources block."""
    dim = PestelDimension(summary="s", impact_analysis="i")
    report = PestelReport(
        topic="Empty Topic",
        executive_summary="exec",
        political=dim,
        economic=dim,
        social=dim,
        technological=dim,
        environmental=dim,
        legal=dim,
        synthesis="syn",
        generated_at="2026-04-25",
    )
    html = PestelRenderer().render(report.model_dump())
    assert "No factors identified." in html
    assert "<h3>Sources</h3>" not in html


def test_pestel_crew_has_expected_members() -> None:
    crew_instance = PestelCrew()
    for attr in (
        "political_researcher",
        "economic_researcher",
        "social_researcher",
        "technological_researcher",
        "environmental_researcher",
        "legal_researcher",
        "pestel_reporter",
        "political_research_task",
        "economic_research_task",
        "social_research_task",
        "technological_research_task",
        "environmental_research_task",
        "legal_research_task",
        "format_pestel_report_task",
        "crew",
    ):
        assert hasattr(crew_instance, attr), f"Missing: {attr}"
