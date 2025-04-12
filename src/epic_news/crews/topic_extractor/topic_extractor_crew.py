from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class TopicExtractorCrew():
    """
    Simple topic extractor crew that extracts the main topic from a user request
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def topic_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['topic_extractor'],
            verbose=True
        )

    @task
    def extract_topic_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_topic_task'],
            output_file='output/topics/extracted_topic.txt'
        )

    @crew
    def crew(self) -> Crew:
        """Creates a simple topic extractor crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
