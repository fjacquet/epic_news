from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew


def test_holiday_crew_has_no_content_formatter():
    crew = HolidayPlannerCrew()
    assert not hasattr(crew, "content_formatter")
    built = crew.crew()
    assert len(built.tasks) == 4  # research tasks only, no mega-format task
