"""
Task Orchestration Utilities for Epic News Crews

This module provides utilities for optimizing task orchestration across crews,
enabling better async and parallel execution patterns.
"""

import asyncio
import time
from enum import Enum
from functools import wraps
from typing import Any

from crewai import Process, Task
from loguru import logger


class OrchestrationStrategy(Enum):
    """
    Defines the orchestration strategies for CrewAI processes.
    """

    SEQUENTIAL = Process.sequential
    HIERARCHICAL = Process.hierarchical

    @staticmethod
    def determine_optimal_strategy(tasks: list[Task], dependencies: dict[str, list[str]] | None = None) -> Process:
        """
        Determines the optimal orchestration strategy based on task characteristics.
        """
        if dependencies or len(tasks) <= 2:
            return Process.sequential
        return Process.hierarchical


class TaskGroup:
    """
    Manages a group of tasks that can be executed with different strategies.
    """

    def __init__(self, tasks: list[Task], dependencies: dict[str, list[str]] | None = None):
        """
        Initialize a TaskGroup.
        """
        self.tasks = tasks
        self.dependencies = dependencies or {}
        self.results: dict[str, Any] = {}

    def get_optimal_process(self) -> Process:
        """
        Get the optimal process strategy for this task group.
        """
        return OrchestrationStrategy.determine_optimal_strategy(self.tasks, self.dependencies)

    def set_all_async(self, async_value: bool = True) -> None:
        """
        Set all tasks in the group to be async or not.
        """
        for task in self.tasks:
            task.async_execution = async_value


def performance_monitor(func):
    """
    Decorator to monitor the performance of crew execution.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting execution of {func.__name__}")
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Completed {func.__name__} in {duration:.2f} seconds")
        return result

    return wrapper


async def execute_tasks_in_parallel(tasks: list[Task], max_concurrent: int = 3) -> dict[str, Any]:
    """
    Execute multiple tasks in parallel with a concurrency limit.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def execute_task(task):
        async with semaphore:
            logger.info(f"Starting task: {task.description[:50]}...")
            task.async_execution = True
            result = await task.execute_async()
            logger.info(f"Completed task: {task.description[:50]}...")
            return task.id, result

    task_coroutines = [execute_task(task) for task in tasks]
    task_results = await asyncio.gather(*task_coroutines)

    for task_id, result in task_results:
        results[task_id] = result

    return results
