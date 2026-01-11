import logging
from typing import Any, cast

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.post_result import PostResult

# Load environment variables
load_dotenv()


@CrewBase
class PostCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def distributor(self) -> Agent:
        return Agent(
            config=cast(dict[str, Any], self.agents_config)["distributor"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
        )

    @task
    def distribution_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=cast(dict[str, Any], self.tasks_config)["distribution_task"],
            agent=self.distributor(),  # type: ignore[call-arg]
            tools=self._get_send_tools() + [FileReadTool()],
            output_pydantic=PostResult,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=cast(list[Agent], self.agents),  # type: ignore[arg-type, attr-defined]
            tasks=cast(list[Task], self.tasks),  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
            memory=False,
            cache=False,
        )

    def _get_send_tools(self):
        """Get email send tools from Composio using new 1.0 API.

        Uses the get_gmail_email_tools() method which explicitly requests
        GMAIL_SEND_EMAIL and other send tools to work around the toolkit
        pagination limitation.

        Returns:
            List of Gmail send tools, or empty list if not available.
        """
        try:
            from epic_news.config.composio_config import ComposioConfig

            # Initialize Composio with new 1.0 API
            composio = ComposioConfig()

            # Get Gmail tools with send functionality explicitly requested
            gmail_tools = composio.get_gmail_email_tools(include_send=True)

            # Filter to only send-related tools
            send_tool_names = ["GMAIL_SEND_EMAIL", "GMAIL_SEND_DRAFT", "GMAIL_REPLY_TO_THREAD"]
            gmail_send_tools = [t for t in gmail_tools if any(n in t.name for n in send_tool_names)]

            if gmail_send_tools:
                logging.getLogger(__name__).info(
                    "Loaded {} Gmail send tools: {}",
                    len(gmail_send_tools),
                    [t.name for t in gmail_send_tools],
                )
                return gmail_send_tools

            # Fallback to draft creation if send tools unavailable
            gmail_draft_tools = [t for t in gmail_tools if "GMAIL_CREATE_EMAIL_DRAFT" in t.name]

            if gmail_draft_tools:
                logging.getLogger(__name__).warning(
                    "GMAIL_SEND_EMAIL not returned, falling back to GMAIL_CREATE_EMAIL_DRAFT"
                )
                return gmail_draft_tools

            logging.getLogger(__name__).warning("No Gmail send/draft tools available")
            return []

        except Exception as e:
            logging.getLogger(__name__).warning(
                "Composio not available; email sending tools disabled. Reason: {}",
                e,
            )
            return []
