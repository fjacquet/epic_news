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
        from composio_crewai import ComposioToolSet

        return ComposioToolSet()

    def _get_send_tools(self):
        toolset = self._get_composio_toolset()
        return toolset.get_tools(actions=["GMAIL_SEND_EMAIL"])
