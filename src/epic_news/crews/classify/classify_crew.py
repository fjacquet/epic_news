from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

load_dotenv()


@CrewBase
class ClassifyCrew():
    """
    Simple classification crew that analyzes user content and classifies it 
    into the appropriate category from a predefined list.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def classifier(self) -> Agent:
        return Agent(
            config=self.agents_config['classifier'],
            verbose=True
        )

    @task
    def classification_task(self) -> Task:
        return Task(
            config=self.tasks_config['classification_task'],
            verbose=True
        )

    @crew
    def crew(self) -> Crew:
        """Creates a simple classification crew"""
        result = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
        return result
    
    def parse_result(self, result, categories=None):
        """
        Extract the selected category from the classification result
        
        Args:
            result (CrewOutput or str): The result from the classification task
            categories (dict, optional): Dictionary of valid categories
            
        Returns:
            str: The selected category (selected_crew)
        """
        # Convert CrewOutput to string if needed
        result_text = str(result)
        
        # The format is now simplified - the category should be the first line
        if not result_text:
            return "UNKNOWN"
            
        # Get the first line which should be the category
        category = result_text.strip().split('\n')[0].strip()
        
        # If categories provided, validate the result
        if categories and category:
            # Case-insensitive match against available categories
            for key in categories:
                if key.upper() == category.upper():
                    return key
        
        # Return the found category or default to UNKNOWN
        return category if category else "UNKNOWN"
