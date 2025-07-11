import os

from composio_crewai import ComposioToolSet
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

toolset = ComposioToolSet()
send_tools = toolset.get_tools(actions=["GMAIL_SEND_EMAIL"])


# Define file reading function decorated as a CrewAI tool
@tool("Read file content")
def read_file_content(file_path: str) -> str:
    """
    Read and return the content of a file.

    Args:
        file_path (str): Path to the file (can be absolute or relative)

    Returns:
        str: Content of the file as a string
    """
    try:
        # Handle both absolute and relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        # Read and return the file content
        with open(file_path, encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


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
            tools=send_tools + [read_file_content],
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
            manager_llm_timeout=300,  # 5 minutes timeout for manager LLM
            task_timeout=600,  # 10 minutes timeout for each task
        )
