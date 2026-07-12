"""Regression: a multi-stop road-trip request produced no report and emailed the
classifier's decision.md instead.

A real run of a Montreux→Montpellier→Anglet→Poitiers→Bourges request had extraction
leave ``destination_location`` (and origin/duration/traveler) ``None`` — the request
describes a *route*, not a single destination. ``generate_holiday_plan`` then silently
early-returned, leaving ``state.output_file`` at ``output/classify/decision.md``, and
``send_email`` mailed that classification JSON as if it were the itinerary.

Two guarantees are locked in here:
  1. Missing ``destination`` falls back to the raw request so the crew still runs.
  2. ``send_email`` refuses to deliver the classifier decision as a report.
"""

from collections import defaultdict
from pathlib import Path

import epic_news.main as main_mod
from epic_news.main import CLASSIFY_DECISION_FILE, ReceptionFlow


def _stub_crew_internals(monkeypatch):
    monkeypatch.setattr(
        main_mod, "kickoff_flow", lambda *a, **k: type("O", (), {"raw": "{}", "pydantic": None})()
    )
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "load_or_parse_model", lambda *a, **k: object())
    monkeypatch.setattr(main_mod, "render_and_write_html", lambda crew, model, path: Path(path))


def test_holiday_falls_back_to_enriched_brief_when_no_destination(monkeypatch):
    flow = ReceptionFlow(user_request="x")
    flow.state.user_request = "raw messy request through Montpellier, Anglet, Poitiers, Bourges"
    # The enrich step produced a clean brief; the fallback must prefer it over the raw
    # request so the crew gets the clean text, not the 8 KB raw blob.
    flow.state.enriched_brief = "Family road trip: Montpellier, Anglet, Poitiers, Bourges"
    _stub_crew_internals(monkeypatch)

    # Extraction left every structured travel field empty -> no "destination" key.
    monkeypatch.setattr(
        type(flow.state), "to_crew_inputs", lambda self: defaultdict(str, {"topic": "vacation"})
    )

    captured = {}
    real_kickoff = main_mod.kickoff_flow

    def capture_kickoff(crew, inputs, *a, **k):
        captured.update(inputs)
        return real_kickoff(crew, inputs, *a, **k)

    monkeypatch.setattr(main_mod, "kickoff_flow", capture_kickoff)

    flow.generate_holiday_plan()

    # The crew actually ran and the itinerary is the report, not decision.md.
    assert flow.state.output_file == "output/holiday/itinerary.html"
    assert captured.get("destination"), "destination must be populated for the crew to run"
    # The fallback prefers the clean enriched brief over the raw request.
    assert captured["destination"] == "Family road trip: Montpellier, Anglet, Poitiers, Bourges"


def test_send_email_refuses_to_deliver_classification_decision(monkeypatch):
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "true")
    flow = ReceptionFlow(user_request="x")
    flow.state.sendto = "someone@example.com"
    flow.state.output_file = CLASSIFY_DECISION_FILE  # report never generated
    flow.state.email_sent = False

    def must_not_send(**_kw):  # pragma: no cover - must not be reached
        raise AssertionError("must not email the classifier decision as a report")

    monkeypatch.setattr(main_mod, "send_report_email", must_not_send)

    flow.send_email()

    assert flow.state.email_sent is False
