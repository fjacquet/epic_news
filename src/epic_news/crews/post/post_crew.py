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

    def _get_send_tools(self):
        """Get email send tools from Composio using new 1.0 API.

        NOTE: Composio 1.0 Gmail integration does NOT include GMAIL_SEND_EMAIL.
        Available Gmail actions: CREATE_EMAIL_DRAFT, FORWARD_MESSAGE, etc.
        The deprecated GMAIL_SEND_EMAIL action from old ComposioToolSet no longer exists.

        Returns:
            List of Gmail tools, or empty list if not available.
        """
        try:
            from epic_news.config.composio_config import ComposioConfig

            # Initialize Composio with new 1.0 API
            composio = ComposioConfig()

            # Get communication tools (includes Gmail)
            comm_tools = composio.get_communication_tools()

            # Try to find GMAIL_SEND_EMAIL (will likely be empty)
            gmail_send_tools = [t for t in comm_tools if "GMAIL_SEND_EMAIL" in t.name]

            if not gmail_send_tools:
                # Alternative: use draft creation instead
                gmail_draft_tools = [t for t in comm_tools if "GMAIL_CREATE_EMAIL_DRAFT" in t.name]

                if gmail_draft_tools:
                    logging.getLogger(__name__).warning(
                        "GMAIL_SEND_EMAIL not available in Composio 1.0. Using GMAIL_CREATE_EMAIL_DRAFT instead."
                    )
                    return gmail_draft_tools
                logging.getLogger(__name__).warning("No Gmail send/draft tools available in Composio 1.0")
                return []

            return gmail_send_tools

        except Exception as e:
            logging.getLogger(__name__).warning(
                "Composio not available; email sending tools disabled. Reason: %s",
                e,
            )
            return []
