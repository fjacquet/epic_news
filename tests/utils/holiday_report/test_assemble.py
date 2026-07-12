from pathlib import Path
from types import SimpleNamespace

from docx import Document

from epic_news.utils.holiday_report import assemble_holiday_docx


class StubLLM:
    """Returns a day-list for the skeleton call, Markdown for everything else."""

    def call(self, messages):
        user = messages[-1]["content"]
        if "date" in messages[0]["content"] and "stops" in messages[0]["content"]:
            return '[{"date":"J1","label":"Montreux","stops":["Montreux"]}]'
        return f"## Section\nContenu pour: {user[:20]}"


def _crew_result():
    outs = ["destination research", "accommodation+dining", "itinerary", "budget"]
    return SimpleNamespace(tasks_output=[SimpleNamespace(raw=o) for o in outs])


def test_assemble_builds_docx_with_sections_and_days(tmp_path: Path):
    out = tmp_path / "guide.docx"
    inputs = {
        "destination": "France",
        "duration": "2 semaines",
        "family": "3",
        "origin": "Montreux",
        "user_preferences_and_constraints": "nature",
    }
    path = assemble_holiday_docx(_crew_result(), inputs, str(out), llm=StubLLM())
    assert path == str(out)
    text = "\n".join(p.text for p in Document(str(out)).paragraphs)
    assert "Introduction" in text
    assert "Itinéraire" in text  # at least one day section
    assert "Budget" in text
