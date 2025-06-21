"""Pydantic models for the Todoist tool."""
from typing import Optional

from pydantic import BaseModel, Field


class TodoistToolInput(BaseModel):
    """Input schema for TodoistTool."""

    action: str = Field(
        ...,
        description="The action to perform: 'get_tasks', 'create_task', 'complete_task', 'get_projects'."
    )
    project_id: Optional[str] = Field(
        None,
        description="The ID of the project to interact with (optional for some actions)."
    )
    task_id: Optional[str] = Field(
        None,
        description="The ID of the task to interact with (required for complete_task)."
    )
    task_content: Optional[str] = Field(
        None,
        description="The content of the task to create (required for create_task)."
    )
    due_string: Optional[str] = Field(
        None,
        description="Due date as a string (e.g., 'today', 'tomorrow', 'next Monday')."
    )
    priority: Optional[int] = Field(
        None,
        description="Task priority (1-4, where 4 is highest)."
    )
