from typing import Type, Optional, List, Dict, Any
import os

from crewai.tools import BaseTool
from pydantic import BaseModel
import requests

from src.epic_news.models.todoist_models import TodoistToolInput


class TodoistTool(BaseTool):
    name: str = "todoist_tool"
    description: str = (
        "A tool for interacting with the Todoist API. "
        "Can get tasks, create tasks, complete tasks, and get projects. "
        "Requires a valid Todoist API token set as TODOIST_API_KEY environment variable."
    )
    args_schema: Type[BaseModel] = TodoistToolInput
    base_url: str = "https://api.todoist.com/rest/v2"

    def _get_headers(self):
        api_token = os.getenv('TODOIST_API_KEY')
        if not api_token:
            raise ValueError("TODOIST_API_KEY environment variable not set. Please set it in your .env file.")
        return {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def _run(
        self,
        action: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        task_content: Optional[str] = None,
        due_string: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> str:
        """Run the Todoist tool with the specified action and parameters."""
        try:
            if action == "get_tasks":
                return self._get_tasks(project_id)
            elif action == "create_task":
                if not task_content:
                    return "Error: task_content is required for create_task action"
                return self._create_task(task_content, project_id, due_string, priority)
            elif action == "complete_task":
                if not task_id:
                    return "Error: task_id is required for complete_task action"
                return self._complete_task(task_id)
            elif action == "get_projects":
                return self._get_projects()
            else:
                return f"Error: Unknown action '{action}'. Valid actions are: get_tasks, create_task, complete_task, get_projects."
        except ValueError as e:
            return f"Error: {e}"

    def _get_tasks(self, project_id: Optional[str] = None) -> str:
        """Get tasks from Todoist, optionally filtered by project."""
        url = f"{self.base_url}/tasks"
        params = {}
        if project_id:
            params["project_id"] = project_id
            
        response = requests.get(url, headers=self._get_headers(), params=params)
        
        if response.status_code == 200:
            tasks = response.json()
            return f"Found {len(tasks)} tasks: {tasks}"
        else:
            return f"Error fetching tasks: {response.status_code} - {response.text}"
    
    def _create_task(
        self,
        content: str,
        project_id: Optional[str] = None,
        due_string: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> str:
        """Create a new task in Todoist."""
        url = f"{self.base_url}/tasks"
        payload: Dict[str, Any] = {"content": content}
        
        if project_id:
            payload["project_id"] = project_id
        if due_string:
            payload["due_string"] = due_string
        if priority:
            payload["priority"] = priority
            
        response = requests.post(url, headers=self._get_headers(), json=payload)
        
        if response.status_code == 200:
            task = response.json()
            return f"Task created successfully: {task}"
        else:
            return f"Error creating task: {response.status_code} - {response.text}"
    
    def _complete_task(self, task_id: str) -> str:
        """Mark a task as complete in Todoist."""
        url = f"{self.base_url}/tasks/{task_id}/close"
        response = requests.post(url, headers=self._get_headers())
        
        if response.status_code == 204:
            return f"Task {task_id} completed successfully"
        else:
            return f"Error completing task: {response.status_code} - {response.text}"
    
    def _get_projects(self) -> str:
        """Get all projects from Todoist."""
        url = f"{self.base_url}/projects"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            projects = response.json()
            return f"Found {len(projects)} projects: {projects}"
        else:
            return f"Error fetching projects: {response.status_code} - {response.text}"
