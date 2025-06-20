import logging
import os
from typing import Any, Dict, List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.tools.finance_tools import get_yahoo_finance_tools
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.models.report import ReportHTMLOutput

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators



@CrewBase
class MeetingPrepCrew():
    """MeetingPrep crew for preparing comprehensive meeting briefings.
    
    This crew coordinates multiple agents to research, analyze, and prepare
    detailed meeting briefings for business meetings. It follows a sequential 
    process of research, product alignment, sales strategy development, and 
    final briefing preparation.
    
    The crew leverages configuration-driven design with YAML files for agents and tasks,
    and implements asynchronous execution where appropriate for optimal performance.
    """

    # Configuration files for agents and tasks
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    # Output directory for meeting preparation documents
    output_dir = os.path.abspath(os.path.join('output', 'meeting'))
    
    def __init__(self):
        """Initialize the MeetingPrepCrew with default values.
        
        Sets up the initial state with empty values for required fields.
        These values should be populated before calling kickoff().
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize crew inputs
        self.topic = ""
        self.sendto = ""
        self.company = ""
        self.participants = []  # List of meeting participants
        self.context = ""
        self.objective = ""
        self.prior_interactions = ""
        
        # Initialize tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all tools needed by the crew's agents.
        
        This centralizes tool initialization to follow the DRY principle and
        makes it easier to modify tool configurations in one place.
        """
        try:
            # Get tools from centralized tool providers
            self.search_tools = get_search_tools()
            self.scrape_tools = get_scrape_tools()
            self.rag_tools = get_rag_tools()
            self.finance_tools = get_yahoo_finance_tools()
            self.report_tools = get_report_tools()
            
            # Combine tools for agents that need all capabilities
            self.all_research_tools = self.search_tools + self.scrape_tools + self.rag_tools + self.finance_tools
            
            logger.info("Successfully initialized all tools for MeetingPrepCrew")
        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            # Provide fallback empty lists to prevent crew from failing completely
            self.search_tools = []
            self.scrape_tools = []
            self.rag_tools = []
            self.finance_tools = []
            self.all_research_tools = []
            raise
    
    # Agent definitions with improved documentation
    @agent
    def lead_researcher_agent(self) -> Agent:
        """Create a lead researcher agent responsible for gathering information.
        
        This agent conducts comprehensive research about the meeting topic, company,
        and participants to provide a solid foundation for the meeting preparation.
        
        Returns:
            Agent: Configured lead researcher agent with search and research tools
        """
        return Agent(
            config=self.agents_config["lead_researcher_agent"],
            tools=self.all_research_tools,
            allow_delegation=False,
            reasoning=True,
            verbose=True,
            respect_context_window=True,
            llm_timeout=300  # Increased timeout for research tasks
        )

    @agent
    def product_specialist_agent(self) -> Agent:
        """Create a product specialist agent for product-related analysis.
        
        This agent analyzes how the company's products align with the meeting
        objectives and the potential client's needs, providing valuable product insights.
        
        Returns:
            Agent: Configured product specialist agent with necessary tools
        """
        return Agent(
            config=self.agents_config["product_specialist_agent"],
            tools=self.all_research_tools,
            allow_delegation=False,
            verbose=True,
            respect_context_window=True,
            llm_timeout=240
        )

    @agent
    def sales_strategist_agent(self) -> Agent:
        """Create a sales strategist agent for developing sales approaches.
        
        This agent develops strategic sales approaches based on the research
        and product alignment information, focusing on persuasive techniques.
        
        Returns:
            Agent: Configured sales strategist agent with research tools
        """
        return Agent(
            config=self.agents_config["sales_strategist_agent"],
            tools=self.all_research_tools,
            reasoning=True,
            verbose=True,
            respect_context_window=True,
            llm_timeout=240
        )

    @agent
    def briefing_coordinator_agent(self) -> Agent:
        """Create a briefing coordinator agent to compile the final briefing.
        
        This agent synthesizes all information from previous agents to create
        a comprehensive, well-structured meeting briefing document.
        
        Returns:
            Agent: Configured briefing coordinator agent
        """
        return Agent(
            config=self.agents_config["briefing_coordinator_agent"],
            tools=self.report_tools,
            verbose=True,
            respect_context_window=True,
            llm_timeout=180
        )


    @task
    def research_task(self) -> Task:
        """Define the research task for gathering meeting-related information.
        
        This task is assigned to the lead researcher agent and is executed asynchronously
        to efficiently gather information about the meeting topic, company, and participants.
        
        Returns:
            Task: Configured research task from YAML configuration
        """
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.lead_researcher_agent(),
            async_execution=True,  # Enable async for I/O-bound research task
            context=self._get_task_context()
        )

    @task
    def product_alignment_task(self) -> Task:
        """Define the product alignment task for analyzing product fit.
        
        This task is assigned to the product specialist agent and analyzes how
        the company's products align with the meeting objectives and client needs.
        
        Returns:
            Task: Configured product alignment task from YAML configuration
        """
        return Task(
            config=self.tasks_config["product_alignment_task"],
            async_execution=True,  # Enable async for parallel processing
        )

    @task
    def sales_strategy_task(self) -> Task:
        """Define the sales strategy task for developing sales approaches.
        
        This task is assigned to the sales strategist agent and develops
        strategic sales approaches based on the research and product information.
        
        Returns:
            Task: Configured sales strategy task from YAML configuration
        """
        return Task(
            config=self.tasks_config["sales_strategy_task"],
            async_execution=True,  # Enable async for parallel processing
        )

    @task
    def meeting_preparation_task(self) -> Task:
        """Define the meeting preparation task for creating the final briefing.
        
        This task is assigned to the briefing coordinator agent and produces a
        comprehensive HTML document with the complete meeting briefing.
        This is the final task and must be synchronous per CrewAI framework requirements.
        
        Returns:
            Task: Configured meeting preparation task from YAML configuration
        """
       
        return Task(
            config=self.tasks_config["meeting_preparation_task"],
            output_pydantic=ReportHTMLOutput,
        )
        
    def _get_task_context(self) -> List[Dict[str, Any]]:
        """Prepare context data for tasks.
        
        This helper method centralizes the creation of context data for tasks,
        following the DRY principle and ensuring consistent data across all tasks.
        
        Returns:
            List[Dict[str, Any]]: List of context dictionaries for task execution
        """
        # Create context items with all necessary information for the tasks
        context = [
            {"topic": self.topic},
            {"company": self.company},
            {"participants": ", ".join(self.participants) if self.participants else ""},
            {"objective": self.objective},
            {"prior_interactions": self.prior_interactions},
            {"context": self.context}
        ]
        
        # Filter out empty context items
        return [item for item in context if list(item.values())[0]]
    
    @crew
    def crew(self) -> Crew:
        """Creates the MeetingPrep crew with configured agents and tasks.
        
        This method sets up the crew with all agents and tasks, configuring
        the process to be sequential to ensure proper information flow between tasks.
        Error handling is implemented to gracefully handle failures.
        
        Returns:
            Crew: Configured crew ready for execution
        """
        try:
            logger.info(f"Creating MeetingPrep crew for topic: {self.topic}")
            
            return Crew(
                agents=self.agents,  # Automatically created by the @agent decorator
                tasks=self.tasks,   # Automatically created by the @task decorator
                process=Process.sequential,  # Tasks must execute in order
                verbose=True,
                llm_timeout=300,     # Overall timeout for LLM operations
                memory=True,        # Enable memory to share information between tasks
                max_rpm=10,         # Rate limit API calls to avoid throttling
                # process=Process.hierarchical could be used for more complex workflows
            )
        except Exception as e:
            logger.error(f"Error creating MeetingPrep crew: {str(e)}")
            raise
    