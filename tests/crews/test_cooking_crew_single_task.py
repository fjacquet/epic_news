from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.models.crews.cooking_recipe import PaprikaRecipe


def test_cooking_crew_is_one_agent_one_task():
    crew = CookingCrew().crew()
    assert len(crew.agents) == 1 and len(crew.tasks) == 1
    assert crew.tasks[0].output_pydantic is PaprikaRecipe
