"""Every report-producing flow method must point state.output_file at the
rendered HTML (not the intermediate JSON) so the Streamlit UI / API can locate
the report. Regression guard for the output_file bug class (see CHANGELOG 3.3.2).

Heavy internals (crew kickoff, model parsing, HTML rendering) are stubbed — this
asserts only the output_file wiring, with no LLM calls or file writes.
"""

from collections import defaultdict
from pathlib import Path

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow

# method name -> expected rendered output path
CASES = [
    ("generate_poem", "output/poem/poem.html"),
    ("generate_news_company", "output/company_news/report.html"),
    ("generate_findaily", "output/findaily/report.html"),
    ("generate_saint_daily", "output/saint_daily/report.html"),
    ("generate_meeting_prep", "output/meeting/meeting_preparation.html"),
    ("generate_book_summary", "output/library/book_summary.html"),
    # holiday now assembles a DOCX travel guide from bounded research fragments,
    # not a rendered HTML report (see assemble_holiday_docx).
    ("generate_holiday_plan", "output/holiday/itinerary.docx"),
    ("generate_news_daily", "output/news_daily/final_report.html"),
]


@pytest.mark.parametrize("method,expected_html", CASES, ids=[c[0] for c in CASES])
def test_generate_sets_output_file_to_rendered_html(method, expected_html, monkeypatch):
    flow = ReceptionFlow(user_request="x")

    monkeypatch.setattr(
        main_mod, "kickoff_flow", lambda *a, **k: type("O", (), {"raw": "{}", "pydantic": None})()
    )
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "load_or_parse_model", lambda *a, **k: object())
    monkeypatch.setattr(main_mod, "render_and_write_html", lambda crew, model, path: Path(path))
    monkeypatch.setattr(main_mod, "assemble_holiday_docx", lambda *a, **k: None)
    # Satisfy per-method preconditions (e.g. holiday needs a destination,
    # meeting_prep needs a company) without touching real crew inputs. The state
    # is a frozen Pydantic model, so patch the class method; defaultdict(str)
    # keeps any unlisted key access from raising KeyError.
    monkeypatch.setattr(
        type(flow.state),
        "to_crew_inputs",
        lambda self: defaultdict(str, {"destination": "Paris", "company": "ACME", "topic": "t"}),
    )

    getattr(flow, method)()

    assert flow.state.output_file == expected_html
