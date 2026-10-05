from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from epic_news.main import ReceptionFlow


def test_shopping_advice_topic_cannot_escape_output_dir(tmp_path, monkeypatch):
    """A hostile topic must be slugified with create_topic_slug, never used as a raw path segment."""
    monkeypatch.chdir(tmp_path)
    flow = ReceptionFlow(user_request="x")
    flow.state.extracted_info = MagicMock(topic="../../Évier / ../etc/passwd")
    advice = MagicMock()
    advice.product_info.name = "Evier"

    with (
        patch("epic_news.main.ShoppingAdvisorCrew"),
        patch("epic_news.main.kickoff_flow", return_value=SimpleNamespace(pydantic=advice)),
        patch("epic_news.main.dump_crewai_state"),
        patch(
            "epic_news.main.assemble_shopping_docx", side_effect=lambda model, inputs, path: path
        ) as assemble,
    ):
        flow.generate_shopping_advice()

    docx_file = assemble.call_args.args[2]
    assert docx_file == "output/shopping_advisor/shopping-advice-evier-etcpasswd.docx"
    assert flow.state.output_file == docx_file
    assert Path(docx_file).resolve().is_relative_to((tmp_path / "output").resolve())


def test_shopping_advice_without_a_structured_output_stops_the_run(tmp_path, monkeypatch):
    """No ShoppingAdviceOutput means no report: the step must raise, not return quietly."""
    monkeypatch.chdir(tmp_path)
    flow = ReceptionFlow(user_request="x")

    with (
        patch("epic_news.main.ShoppingAdvisorCrew"),
        patch(
            "epic_news.main.kickoff_flow",
            return_value=SimpleNamespace(pydantic=None, tasks_output=[SimpleNamespace(pydantic=None)]),
        ),
        patch("epic_news.main.dump_crewai_state"),
        patch("epic_news.main.assemble_shopping_docx") as assemble,
        pytest.raises(RuntimeError, match="ShoppingAdviceOutput"),
    ):
        flow.generate_shopping_advice()

    assemble.assert_not_called()
