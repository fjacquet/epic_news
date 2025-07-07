import pytest
from crewai import Process, Task
from loguru import logger

from epic_news.utils.task_orchestration import (
    OrchestrationStrategy,
    TaskGroup,
    execute_tasks_in_parallel,
    performance_monitor,
)


def test_determine_optimal_strategy():
    # Test that determine_optimal_strategy determines the optimal orchestration strategy
    tasks = [
        Task(description="Test Task 1", expected_output="Test Output 1", async_execution=True),
        Task(description="Test Task 2", expected_output="Test Output 2", async_execution=True),
        Task(description="Test Task 3", expected_output="Test Output 3", async_execution=True),
    ]
    strategy = OrchestrationStrategy.determine_optimal_strategy(tasks)
    assert strategy == Process.hierarchical


def test_task_group():
    # Test that the TaskGroup manages a group of tasks correctly
    tasks = [
        Task(description="Test Task 1", expected_output="Test Output 1"),
        Task(description="Test Task 2", expected_output="Test Output 2"),
    ]
    task_group = TaskGroup(tasks)
    assert len(task_group.tasks) == 2
    task_group.set_all_async(True)
    for task in task_group.tasks:
        assert task.async_execution


def test_performance_monitor(caplog):
    # Test that the performance_monitor decorator monitors the performance of a function
    logger.add(caplog.handler, format="{message}")
    @performance_monitor
    def test_function():
        pass

    test_function()
    assert "Starting execution" in caplog.text
    assert "Completed" in caplog.text


@pytest.mark.asyncio
async def test_execute_tasks_in_parallel(mocker):
    """Test that execute_tasks_in_parallel executes multiple tasks in parallel correctly."""
    tasks = [
        Task(description="Test Task 1", expected_output="Test Output 1"),
        Task(description="Test Task 2", expected_output="Test Output 2"),
    ]

    # Define an async function to be our mock's side effect
    async def mock_async_execute(*args, **kwargs):
        return "test_result"

    # Mock the async execution of a task
    mocker.patch("crewai.task.Task.execute_async", side_effect=mock_async_execute)

    # Call the function under test
    results = await execute_tasks_in_parallel(tasks)

    # Verify that the results are correct
    assert len(results) == len(tasks)
    assert all(result == "test_result" for result in results.values())

    # Verify that the result keys match the task IDs
    task_ids = {task.id for task in tasks}
    assert set(results.keys()) == task_ids
