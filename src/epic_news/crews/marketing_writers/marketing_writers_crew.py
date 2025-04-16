from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet
import os

# Set up the tools for marketing tasks
toolset = ComposioToolSet()
marketing_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
])

@CrewBase
class MarketingWritersCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
       
    @agent
    def marketing_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["marketing_specialist"],
            tools=marketing_tools,
            verbose=True,
            llm_timeout=300
        )
    
    @agent
    def copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["copywriter"],
            tools=marketing_tools,
            verbose=True,
            llm_timeout=300
        )

    @task
    def analyze_market_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_market_task"],
            agent=self.marketing_specialist(),
            verbose=True,
            llm_timeout=300
        )
        
    @task
    def enhance_message_task(self) -> Task:
        return Task(
            config=self.tasks_config["enhance_message_task"],
            agent=self.copywriter(),
            output_file="output/marketing/enhanced_message.html",
            verbose=True,
            llm_timeout=300
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Marketing Writers crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
        )
