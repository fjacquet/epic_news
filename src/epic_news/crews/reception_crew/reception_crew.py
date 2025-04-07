from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import json
import datetime

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class ReceptionCrew():
    """ReceptionCrew crew for routing requests to the appropriate specialized crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, request, topic=None, recipient_email=None):
        """Initialize the ReceptionCrew with the user request and optional topic."""
        self.request = request
        self.topic = topic if topic else "General topic"
        self.recipient_email = recipient_email if recipient_email else "user@example.com"
        self.current_year = datetime.datetime.now().year
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def router(self) -> Agent:
        return Agent(
            config=self.agents_config['router'],
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def routing_task(self) -> Task:
        # Create a custom task description with the actual request and topic values
        custom_description = f"""
        Analyze the user request and determine which specialized crew should handle it.
        
        The user request is: "{self.request}"
        The topic is: "{self.topic}"
        
        Based on your analysis, classify the request into one of the following categories:
        
        1. NEWS - If the request is about current events, news topics, research, etc.
        2. POEM - If the request is about creative writing, poetry, artistic expression, etc.
        3. COOKING - If the request is about food, recipes, culinary topics, etc.
        4. UNKNOWN - If the request doesn't clearly fit into any of the above categories.
        """
        
        # Create a task based on the YAML config but override the description
        task = Task(
            config=self.tasks_config['routing_task'],
            context=[
                {
                    "request": self.request,
                    "topic": self.topic,
                    "expected_output": "A clear decision on which crew should handle the request."
                }
            ]
        )
        
        # Override the description with our custom one
        task.description = custom_description
        
        return task

    @crew
    def crew(self) -> Crew:
        """Creates the ReceptionCrew for routing requests"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
    
    def route_request(self):
        """Route the request to the appropriate crew based on keywords in the request."""
        # First, try to determine crew type based on keywords in the request
        request_lower = self.request.lower()
        
        if any(word in request_lower for word in ["poeme", "poem", "poetry", "verse", "stanza"]):
            crew_type = "POEM"
        elif any(word in request_lower for word in ["recette", "recipe", "cook", "cuisine", "food", "meal", "dish", "ingredient", "quiche", "saumon", "asperges"]):
            crew_type = "COOKING"
        elif any(word in request_lower for word in ["news", "actualité", "information", "article", "report"]):
            crew_type = "NEWS"
        else:
            # If no keywords match, use the AI routing task as a fallback
            try:
                result = self.crew().kickoff()
                raw_result = result.raw
                
                # Try to parse the result as JSON (with or without code blocks)
                if raw_result.startswith("```json") and raw_result.endswith("```"):
                    json_content = raw_result.replace("```json", "").replace("```", "").strip()
                    routing_decision = json.loads(json_content)
                else:
                    routing_decision = json.loads(raw_result)
                
                # Extract crew type from the routing decision
                crew_type = routing_decision.get("crew_type", "UNKNOWN")
                
                # If AI couldn't determine a crew type, mark as unknown
                if not crew_type or crew_type == "{crew_type}":
                    crew_type = "UNKNOWN"
                    
            except Exception as e:
                # If there's any error in the AI routing, default to UNKNOWN
                print(f"Error in AI routing: {str(e)}")
                crew_type = "UNKNOWN"
        
        # Return a simple dictionary with the crew type and other optional fields
        return {
            "crew_type": crew_type,
            "topic": self.topic
        }
