from composio_crewai import ComposioToolSet
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

toolset = ComposioToolSet()
send_tools = toolset.get_tools(actions=["GMAIL_SEND_EMAIL"])


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
            tools=send_tools + [FileReadTool()],
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
