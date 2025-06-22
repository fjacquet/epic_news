"""Pydantic models for the Todoist tool."""

from pydantic import BaseModel, Field


class TodoistToolInput(BaseModel):
    """Input schema for TodoistTool."""

    action: str = Field(
        ...,
        description="The action to perform: 'get_tasks', 'create_task', 'complete_task', 'get_projects'."
    )
    project_id: str | None = Field(
        None,
        description="The ID of the project to interact with (optional for some actions)."
    )
    task_id: str | None = Field(
        None,
        description="The ID of the task to interact with (required for complete_task)."
    )
    task_content: str | None = Field(
        None,
        description="The content of the task to create (required for create_task)."
    )
    due_string: str | None = Field(
        None,
        description="Due date as a string (e.g., 'today', 'tomorrow', 'next Monday')."
    )
    priority: int | None = Field(
        None,
        description="Task priority (1-4, where 4 is highest)."
    )
