"""Structural tests for the PESTEL crew ."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from epic_news.crews.pestel.pestel_crew import PestelCrew
from epic_news.models.content_state import CrewCategories
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


def test_pestel_category_registered() -> None:
    assert CrewCategories.PESTEL == "PESTEL"
    assert CrewCategories.to_dict().get("PESTEL") == "PESTEL"


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
