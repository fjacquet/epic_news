
import logging
from unittest.mock import MagicMock, patch
from epic_news.utils.task_orchestration import OrchestrationStrategy, TaskGroup, performance_monitor, execute_tasks_in_parallel
from crewai import Task, Process
import pytest
import asyncio

def test_determine_optimal_strategy():
    # Test that determine_optimal_strategy determines the optimal orchestration strategy
    tasks = [Task(description="Test Task 1", expected_output="Test Output 1", async_execution=True), Task(description="Test Task 2", expected_output="Test Output 2", async_execution=True)]
    strategy = OrchestrationStrategy.determine_optimal_strategy(tasks)
    assert strategy == Process.hierarchical

def test_task_group():
    # Test that the TaskGroup manages a group of tasks correctly
    tasks = [Task(description="Test Task 1", expected_output="Test Output 1"), Task(description="Test Task 2", expected_output="Test Output 2")]
    task_group = TaskGroup(tasks)
    assert len(task_group.tasks) == 2
    task_group.set_all_async(True)
    for task in task_group.tasks:
        assert task.async_execution

def test_performance_monitor(caplog):
    # Test that the performance_monitor decorator monitors the performance of a function
    @performance_monitor
    def test_function():
        pass
    with caplog.at_level(logging.INFO):
        test_function()
    assert "Starting execution" in caplog.text
    assert "Completed" in caplog.text

@pytest.mark.asyncio
async def test_execute_tasks_in_parallel(mocker):
    # Test that execute_tasks_in_parallel executes multiple tasks in parallel
    tasks = [Task(description="Test Task 1", expected_output="Test Output 1"), Task(description="Test Task 2", expected_output="Test Output 2")]
    
    async def mock_execute_async(self):
        return "test"

    mocker.patch('crewai.task.Task.execute_async', mock_execute_async)
    
    async def mock_gather(*args, **kwargs):
        return [("task1", "result1"), ("task2", "result2")]

    mocker.patch('asyncio.gather', mock_gather)
    mocker.patch('asyncio.Semaphore')

    results = await execute_tasks_in_parallel(tasks)
    assert len(results) == 2
    assert results["task1"] == "result1"
