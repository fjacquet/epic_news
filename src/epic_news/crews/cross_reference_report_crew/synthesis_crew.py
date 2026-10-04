"""Cross-reference report by synthesis: one tool-free task over the six OSINT reports.

Alternative to CrossReferenceReportCrew (which re-researches the target); selected with
CROSS_REFERENCE_MODE=synthesis while the two are compared (efficiency spec E6).
"""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.cross_reference_report import CrossReferenceReport


@CrewBase
class CrossReferenceSynthesisCrew:
    """Synthesise the OSINT reports into one CrossReferenceReport."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]
    tasks_config: dict[str, Any] = "config/synthesis_tasks.yaml"  # type: ignore[assignment]

    @agent
    def osint_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["osint_reporter"],
            tools=[],
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def osint_synthesis(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["osint_synthesis"],
            output_pydantic=CrossReferenceReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
