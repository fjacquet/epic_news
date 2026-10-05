import json

from epic_news.crews.cross_reference_report_crew.cross_reference_report_crew import CrossReferenceReportCrew
from epic_news.main import OSINT_REPORT_MAX_CHARS, _load_osint_reports
from epic_news.models.crews.cross_reference_report import OSINT_AREAS, CrossReferenceReport

TASKS = [
    "intelligence_requirements_planning",
    "intelligence_collection_coordination",
    "intelligence_analysis_integration",
    "intelligence_product_development",
    "global_reporting",
]


def test_tasks_use_yaml_text_with_target_placeholder():
    crew = CrossReferenceReportCrew()
    tasks = {t.name: t for t in crew.crew().tasks}
    assert set(tasks) == set(TASKS)
    for name in TASKS:
        assert "{target}" in tasks[name].description, name
        assert "{target}" in tasks[name].expected_output, name
    assert "{osint_reports}" in tasks["global_reporting"].description
    assert "directory_read_tool" not in tasks["global_reporting"].description
    assert "detailed_findings" in tasks["global_reporting"].expected_output


def test_load_osint_reports_skips_missing_and_caps(tmp_path):
    (tmp_path / "company_profile.json").write_text(json.dumps({"name": "Logitech"}))
    (tmp_path / "tech_stack.json").write_text(json.dumps({"blob": "x" * (OSINT_REPORT_MAX_CHARS * 2)}))
    (tmp_path / "web_presence.json").write_text("not json")
    text = _load_osint_reports(tmp_path)
    assert '"company_profile": {"name": "Logitech"}' in text
    assert "...[truncated]" in text
    assert "web_presence" not in text and "hr_intelligence" not in text


def test_detailed_findings_schema_lists_the_osint_areas():
    schema = CrossReferenceReport.model_json_schema()["properties"]["detailed_findings"]
    assert set(schema["properties"]) == set(OSINT_AREAS)
    assert CrossReferenceReport(
        target="X", executive_summary="s", detailed_findings={"a": 1}, confidence_assessment="c"
    ).detailed_findings == {"a": 1}
