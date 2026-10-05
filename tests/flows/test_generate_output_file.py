"""Every report-producing flow method must point state.output_file at the
DOCX report (not the intermediate JSON) so the Streamlit UI / API can locate
the report. Regression guard for the output_file bug class (see CHANGELOG 3.3.2).

Heavy internals (crew kickoff, model parsing, DOCX assembly) are stubbed — this
asserts only the output_file wiring, with no LLM calls or file writes.
"""

from collections import defaultdict

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow

# method name -> expected report path
CASES = [
    ("generate_poem", "output/poem/poem.docx"),
    ("generate_news_company", "output/company_news/report.docx"),
    ("generate_findaily", "output/findaily/report.docx"),
    ("generate_saint_daily", "output/saint_daily/report.docx"),
    ("generate_meeting_prep", "output/meeting/meeting_preparation.docx"),
    ("generate_book_summary", "output/library/book_summary.docx"),
    ("generate_holiday_plan", "output/holiday/itinerary.docx"),
    ("generate_news_daily", "output/news_daily/report.docx"),
]


@pytest.mark.parametrize("method,expected", CASES, ids=[c[0] for c in CASES])
def test_generate_sets_output_file_to_the_docx(method, expected, monkeypatch):
    flow = ReceptionFlow(user_request="x")

    monkeypatch.setattr(
        main_mod, "kickoff_flow", lambda *a, **k: type("O", (), {"raw": "{}", "pydantic": None})()
    )
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "load_or_parse_model", lambda *a, **k: object())
    # Every assembler takes (model, inputs, output_path, ...) and returns the path.
    for name in dir(main_mod):
        if name.startswith("assemble_") and name.endswith("_docx"):
            monkeypatch.setattr(main_mod, name, lambda model, inputs, path, *a, **k: path)
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

    assert flow.state.output_file == expected
