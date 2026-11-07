from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew


def test_lodging_and_itinerary_agents_can_look_up_real_places():
    crew = HolidayPlannerCrew()
    for agent in (crew.accommodation_specialist(), crew.itinerary_architect()):
        assert "geoapify_places_search" in {tool.name for tool in agent.tools}


def test_holiday_crew_has_no_content_formatter():
    crew = HolidayPlannerCrew()
    assert not hasattr(crew, "content_formatter")
    built = crew.crew()
    assert len(built.tasks) == 4  # research tasks only, no mega-format task
