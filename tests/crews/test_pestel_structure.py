"""Structural tests for the PESTEL crew and its rendering helper."""

from __future__ import annotations

import pytest

from epic_news.models.crews.pestel_report import PestelDimension, PestelReport


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
    from pydantic import ValidationError

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
    from epic_news.utils.html.template_renderers.pestel_markdown import pestel_to_markdown

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
    assert "https://example.com" in md
    assert "Cross-dim synthesis" in md


def test_pestel_category_registered() -> None:
    from epic_news.models.content_state import CrewCategories

    assert CrewCategories.PESTEL == "PESTEL"
    assert CrewCategories.to_dict().get("PESTEL") == "PESTEL"


def test_pestel_markdown_handles_empty_factors_and_sources() -> None:
    """Empty key_factors → '_(none identified)_'; empty sources → no Sources section."""
    from epic_news.utils.html.template_renderers.pestel_markdown import pestel_to_markdown

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
    from epic_news.utils.html.template_renderers.pestel_markdown import pestel_to_markdown

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
    from pathlib import Path

    import yaml

    config_dir = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "epic_news"
        / "crews"
        / "pestel"
        / "config"
    )
    agents = yaml.safe_load((config_dir / "agents.yaml").read_text(encoding="utf-8"))
    tasks = yaml.safe_load((config_dir / "tasks.yaml").read_text(encoding="utf-8"))

    assert "political_researcher" in agents
    assert "pestel_reporter" in agents
    assert "format_pestel_report_task" in tasks
    # Each researcher task references current_date in its description
    assert "current_date" in tasks["political_research_task"]["description"]


def test_pestel_crew_has_expected_members() -> None:
    from epic_news.crews.pestel.pestel_crew import PestelCrew

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
