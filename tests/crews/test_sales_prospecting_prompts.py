"""The sales prospecting tasks must use their YAML prompts, not literal overrides."""

from pathlib import Path

import pytest
import yaml

from epic_news import main as main_module
from epic_news.crews.sales_prospecting.sales_prospecting_crew import SalesProspectingCrew
from epic_news.main import ReceptionFlow
from epic_news.models.extracted_info import ExtractedInfo

TASKS_YAML = {
    "research_company_task": "research_company_task",
    "analyze_org_structure_task": "analyze_org_structure_task",
    "find_key_contacts_task": "find_key_contacts_task",
    "generate_sales_metrics_task": "develop_approach_strategy_task",
}


class _StopKickoffError(Exception):
    pass


def test_tasks_use_yaml_descriptions() -> None:
    yaml_tasks = yaml.safe_load(
        (
            Path(__file__).parents[2] / "src/epic_news/crews" / "sales_prospecting" / "config" / "tasks.yaml"
        ).read_text()
    )
    crew = SalesProspectingCrew()
    for method, key in TASKS_YAML.items():
        task = getattr(crew, method)()
        assert (
            task.description == yaml_tasks[key]["description"].strip()
            or task.description == yaml_tasks[key]["description"]
        )
        assert "{company}" in task.description
        assert (
            task.expected_output == yaml_tasks[key]["expected_output"].strip()
            or task.expected_output == yaml_tasks[key]["expected_output"]
        )


@pytest.fixture
def captured_inputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    captured: dict = {}

    def fake_kickoff_flow(crew, inputs):
        captured.update(inputs)
        raise _StopKickoffError

    monkeypatch.setattr(main_module, "kickoff_flow", fake_kickoff_flow)
    monkeypatch.setattr(main_module, "SalesProspectingCrew", lambda: object())
    return captured


def test_generate_sales_prospecting_passes_company_and_default_product(captured_inputs) -> None:
    flow = ReceptionFlow(user_request="prospects chez Nestlé")
    flow.state.extracted_info = ExtractedInfo(target_company="Nestlé")
    with pytest.raises(_StopKickoffError):
        flow.generate_sales_prospecting_report()
    assert captured_inputs["company"] == "Nestlé"
    assert captured_inputs["our_product"] == "our product/service"


def test_generate_sales_prospecting_keeps_given_product(captured_inputs) -> None:
    flow = ReceptionFlow(user_request="prospects chez Nestlé")
    flow.state.extracted_info = ExtractedInfo(target_company="Nestlé", our_product="HR suite")
    with pytest.raises(_StopKickoffError):
        flow.generate_sales_prospecting_report()
    assert captured_inputs["our_product"] == "HR suite"
