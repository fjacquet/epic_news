from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool

from src.epic_news.tools.rag_tools import get_rag_tools
from src.epic_news.tools.reporting_tool import ReportingTool
from src.epic_news.tools.save_to_rag_tool import SaveToRagTool
from src.epic_news.tools.unified_rss_tool import UnifiedRssTool


@CrewBase
class RssWeeklyCrew:
    """RssWeeklyCrew crew - Simplified version using UnifiedRssTool"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def content_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['content_summarizer'],
            verbose=True,
            tools=[FileReadTool(), UnifiedRssTool(), SaveToRagTool(), ReportingTool()] + get_rag_tools(),
            reasoning=False,
            respect_context_window=True,
        )

    @task
    def compile_digest_task(self) -> Task:
        return Task(
            config=self.tasks_config['compile_digest_task'],
            async_execution=False
        )

    @crew
    def crew(self) -> Crew:
        """Creates the simplified RSS Weekly crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            respect_context_window=True,
        )
