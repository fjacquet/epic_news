from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import ExchangeRateTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.holiday_planner_report import HolidayPlannerReport
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools, get_youtube_tools

load_dotenv()


@CrewBase
class HolidayPlannerCrew:
    """HolidayPlanner crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def travel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["travel_researcher"],  # type: ignore[index]
            tools=get_search_tools() + get_youtube_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=False,
            reasoning=False,
            max_reasoning_attempts=3,
            allow_delegation=True,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def accommodation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["accommodation_specialist"],  # type: ignore[index]
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=False,
            reasoning=False,
            max_reasoning_attempts=3,
            allow_delegation=True,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["itinerary_architect"],  # type: ignore[index]
            tools=get_search_tools() + get_scrape_tools() + get_youtube_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=False,
            reasoning=False,
            max_reasoning_attempts=3,
            allow_delegation=True,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def budget_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["budget_manager"],  # type: ignore[index]
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def content_formatter(self) -> Agent:
        # No tools: this agent runs the final format_and_translate_guide task, which
        # carries output_pydantic=HolidayPlannerReport. With tools, CrewAI 1.15 can leak
        # a tool-call result (e.g. ExchangeRateTool's {base_currency, target_currencies})
        # into TaskOutput.raw, which then fails HolidayPlannerReport validation. The
        # reporter synthesizes solely from the prior tasks' context (crews/CLAUDE.md
        # two-agent pattern: reporter has no tools = clean structured output).
        return Agent(
            config=self.agents_config["content_formatter"],  # type: ignore[index]
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def research_destination(self) -> Task:
        # Sequential (async_execution=False): CrewAI 1.15's concurrent async task
        # path can leak a tool-call into TaskOutput.raw (which must be a str),
        # crashing the crew ("Input should be a valid string ... ChatCompletion
        # MessageToolCall"). Running these sequentially avoids the concurrency and
        # actually improves data flow (accommodation now sees the research output).
        return Task(config=self.tasks_config["research_destination"], async_execution=False)  # type: ignore[call-arg, arg-type, index]

    @task
    def recommend_accommodation_and_dining(self) -> Task:
        return Task(config=self.tasks_config["recommend_accommodation_and_dining"], async_execution=False)  # type: ignore[call-arg, arg-type, index]

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config["plan_itinerary"],  # type: ignore[call-arg, arg-type, index]
            async_execution=False,
        )

    @task
    def analyze_and_optimize_budget(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_and_optimize_budget"],  # type: ignore[call-arg, arg-type, index]
            async_execution=False,
        )

    @task
    def format_and_translate_guide(self) -> Task:
        return Task(
            config=self.tasks_config["format_and_translate_guide"],  # type: ignore[call-arg, arg-type, index]
            async_execution=False,
            output_pydantic=HolidayPlannerReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),  # type: ignore[call-arg]
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=30,  # Keeping existing custom value
            max_retry_limit=5,
            verbose=False,
        )
