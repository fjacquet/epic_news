from types import SimpleNamespace
from unittest.mock import patch

from epic_news.main import ReceptionFlow


def test_generate_holiday_plan_sets_docx_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    flow = ReceptionFlow(user_request="x")
    flow.state.selected_crew = "HOLIDAY_PLANNER"
    flow.state.enriched_brief = "Voyage en France"

    crew_result = SimpleNamespace(tasks_output=[SimpleNamespace(raw="r") for _ in range(4)])

    with (
        patch("epic_news.main.kickoff_flow", return_value=crew_result),
        patch("epic_news.main.dump_crewai_state"),
        patch("epic_news.main.assemble_holiday_docx", return_value="output/holiday/itinerary.docx") as asm,
    ):
        flow.generate_holiday_plan()

    asm.assert_called_once()
    assert flow.state.output_file.endswith("itinerary.docx")
