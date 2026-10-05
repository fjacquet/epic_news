"""Recorded crew outputs must keep parsing to the same models (simplification S2).

Golden files are model dumps taken with the parser as it was before S2. Regenerate
only on purpose: UPDATE_PARSING_GOLDEN=1 env -u VIRTUAL_ENV uv run pytest <this file>
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news.models.crews.company_profiler_report import CompanyProfileReport
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.models.crews.deep_research_report import DeepResearchReport
from epic_news.models.crews.hr_intelligence_report import HRIntelligenceReport
from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.models.crews.web_presence_report import WebPresenceReport
from epic_news.utils.diagnostics import parse_crewai_output

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "raw_outputs"

CASES = {
    "company_profile": CompanyProfileReport,
    "tech_stack": TechStackReport,
    "web_presence": WebPresenceReport,
    "hr_intelligence": HRIntelligenceReport,
    "cross_reference_report": CrossReferenceReport,
    "deep_research": DeepResearchReport,
    "newsdaily": NewsDailyReport,
    "pestel": PestelReport,
    "sales_prospecting": SalesProspectingReport,
}


@pytest.mark.parametrize("label", sorted(CASES))
def test_recorded_output_parses_to_golden_model(label):
    raw = (FIXTURES / f"{label}.txt").read_text(encoding="utf-8")
    model = parse_crewai_output(SimpleNamespace(raw=raw, output=None), CASES[label])
    dumped = json.loads(model.model_dump_json())
    golden = FIXTURES / "expected" / f"{label}.json"
    if os.getenv("UPDATE_PARSING_GOLDEN") == "1":
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(
            json.dumps(dumped, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
        )
        return
    assert dumped == json.loads(golden.read_text(encoding="utf-8"))
