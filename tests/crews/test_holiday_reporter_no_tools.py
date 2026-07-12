"""The holiday reporter agent must have no tools.

A real HOLIDAY_PLANNER run crashed with::

    1 validation error for HolidayPlannerReport
    introduction  Field required [input_value={'base_currency': 'CHF', 'target_currencies': ['EUR']}]

``content_formatter`` runs the final ``format_and_translate_guide`` task, which
carries ``output_pydantic=HolidayPlannerReport``. Because that agent had tools
(search, scrape, ExchangeRateTool), CrewAI 1.15 leaked a tool-call result — the
ExchangeRateTool output — into ``TaskOutput.raw``, which then failed schema
validation. The project's two-agent pattern (see crews/CLAUDE.md) requires the
reporter to have NO tools so its output is clean structured data. It receives all
upstream data via the sequential task context, not via live tools.
"""

from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew


def test_content_formatter_reporter_has_no_tools():
    formatter = HolidayPlannerCrew().content_formatter()
    assert not formatter.tools, (
        "content_formatter runs the output_pydantic=HolidayPlannerReport task; giving it "
        "tools lets a tool-call result (e.g. ExchangeRateTool) leak into TaskOutput.raw and "
        "fail schema validation. Reporter agents must have no tools."
    )
