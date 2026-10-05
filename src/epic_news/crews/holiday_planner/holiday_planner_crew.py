from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import ExchangeRateTool

from epic_news.config.llm_config import LLMConfig
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools, get_youtube_tools


@CrewBase
class HolidayPlannerCrew:
    """HolidayPlanner crew"""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def travel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["travel_researcher"],
            tools=get_search_tools() + get_youtube_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            verbose=False,
            allow_delegation=True,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def accommodation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["accommodation_specialist"],
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            verbose=False,
            allow_delegation=True,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["itinerary_architect"],
            tools=get_search_tools() + get_scrape_tools() + get_youtube_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            verbose=False,
            allow_delegation=True,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def budget_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["budget_manager"],
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @task
    def research_destination(self) -> Task:
        # Sequential (async_execution=False): CrewAI 1.15's concurrent async task
        # path can leak a tool-call into TaskOutput.raw (which must be a str),
        # crashing the crew ("Input should be a valid string ... ChatCompletion
        # MessageToolCall"). Running these sequentially avoids the concurrency and
        # actually improves data flow (accommodation now sees the research output).
        return Task(config=self.tasks_config["research_destination"], async_execution=False)

    @task
    def recommend_accommodation_and_dining(self) -> Task:
        return Task(config=self.tasks_config["recommend_accommodation_and_dining"], async_execution=False)

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config["plan_itinerary"],
            async_execution=False,
        )

    @task
    def analyze_and_optimize_budget(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_and_optimize_budget"],
            async_execution=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            max_rpm=30,  # Keeping existing custom value
            verbose=False,
        )
