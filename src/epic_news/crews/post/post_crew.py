import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@CrewBase
class PostCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def distributor(self):
        return Agent(config=self.agents_config["distributor"], verbose=True, llm_timeout=300)

    @task
    def distribution_task(self) -> Task:
        return Task(
            config=self.tasks_config["distribution_task"],
            agent=self.distributor(),
            tools=self._get_send_tools() + [FileReadTool()],
            verbose=True,
            llm_timeout=300,
        )

    @crew
    def crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            cache=False,
            manager_llm_timeout=300,
            task_timeout=600,
        )

    def _get_composio_toolset(self):
        try:
            from composio_crewai import ComposioToolSet
        except Exception as e:  # ImportError or runtime issues
            logging.getLogger(__name__).warning(
                "Composio not available; email sending tools disabled. Reason: %s",
                e,
            )
            return None
        try:
            return ComposioToolSet()
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Failed to initialize ComposioToolSet; email sending disabled. Reason: %s",
                e,
            )
            return None

    def _get_send_tools(self):
        toolset = self._get_composio_toolset()
        if toolset is None:
            return []
        try:
            return toolset.get_tools(actions=["GMAIL_SEND_EMAIL"])
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Composio tool retrieval failed; email sending disabled. Reason: %s",
                e,
            )
            return []
