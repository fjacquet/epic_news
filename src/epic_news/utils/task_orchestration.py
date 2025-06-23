"""
Task Orchestration Utilities for Epic News Crews

This module provides utilities for optimizing task orchestration across crews,
enabling better async and parallel execution patterns.
"""

import asyncio
import inspect
import logging
import time
from functools import wraps
from typing import Any

from crewai import Process, Task

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("task_orchestration")


class OrchestrationStrategy:
    """
    Defines different orchestration strategies for crews and tasks.
    """

    SEQUENTIAL = Process.sequential
    HIERARCHICAL = Process.hierarchical

    @staticmethod
    def determine_optimal_strategy(tasks: list[Task], dependencies: dict[str, list[str]] = None) -> Process:
        """
        Determines the optimal orchestration strategy based on task dependencies.

        Args:
            tasks: List of tasks to analyze
            dependencies: Dictionary mapping task IDs to lists of dependency task IDs

        Returns:
            Process: The recommended Process strategy
        """
        if not dependencies:
            # If no explicit dependencies, check for async_execution flags
            async_tasks = [task for task in tasks if getattr(task, "async_execution", False)]
            if len(async_tasks) > len(tasks) / 2:  # If more than half are async
                logger.info("Majority of tasks are async-capable, recommending hierarchical process")
                return Process.hierarchical
            return Process.sequential

        # If we have explicit dependencies, check their structure
        dependency_count = sum(len(deps) for deps in dependencies.values())
        if dependency_count > len(tasks) / 2:
            # Many dependencies - hierarchical is better
            return Process.hierarchical
        return Process.sequential


class TaskGroup:
    """
    Manages a group of tasks that can be executed with different strategies.
    """

    def __init__(self, tasks: list[Task], dependencies: dict[str, list[str]] = None):
        """
        Initialize a TaskGroup.

        Args:
            tasks: List of tasks to manage
            dependencies: Dictionary mapping task IDs to lists of dependency task IDs
        """
        self.tasks = tasks
        self.dependencies = dependencies or {}
        self.results = {}

    def get_optimal_process(self) -> Process:
        """
        Get the optimal process strategy for this task group.

        Returns:
            Process: The recommended Process strategy
        """
        return OrchestrationStrategy.determine_optimal_strategy(self.tasks, self.dependencies)

    def set_all_async(self, async_value: bool = True) -> None:
        """
        Set all tasks in the group to be async or not.

        Args:
            async_value: Boolean value to set for async_execution
        """
        for task in self.tasks:
            task.async_execution = async_value


def performance_monitor(func):
    """
    Decorator to monitor the performance of crew execution.

    Args:
        func: The function to monitor

    Returns:
        Callable: The wrapped function
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

    Args:
        tasks: List of tasks to execute
        max_concurrent: Maximum number of tasks to run concurrently

    Returns:
        Dict[str, Any]: Dictionary of task results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def execute_task(task):
        async with semaphore:
            logger.info(f"Starting task: {task.description[:50]}...")
            # Ensure task is set to async execution
            task.async_execution = True
            # Execute the task
            result = await task.execute_async()
            logger.info(f"Completed task: {task.description[:50]}...")
            return task.id, result

    # Create tasks
    task_coroutines = [execute_task(task) for task in tasks]

    # Execute tasks and gather results
    task_results = await asyncio.gather(*task_coroutines)

    # Process results
    for task_id, result in task_results:
        results[task_id] = result

    return results


def optimize_crew_process(
    crew_module_path: str, process_type: Process | None = None, analyze_only: bool = False
) -> dict[str, Any]:
    """
    Analyzes and optionally updates a crew's process type.

    Args:
        crew_module_path: Path to the crew module
        process_type: Process type to set (if None, will determine optimal)
        analyze_only: If True, only analyze and don't modify

    Returns:
        Dict[str, Any]: Analysis results
    """
    import importlib

    try:
        # Import the module
        module = importlib.import_module(crew_module_path)

        # Find crew classes
        crew_classes = []
        for _, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, "crew"):
                crew_classes.append(obj)

        if not crew_classes:
            return {"error": "No crew classes found in module"}

        results = {}
        for crew_class in crew_classes:
            # Instantiate the crew
            crew_instance = crew_class()

            # Get tasks
            tasks = []
            for name, method in inspect.getmembers(crew_instance):
                if name.endswith("_task") and callable(method):
                    task = method()
                    if isinstance(task, Task):
                        tasks.append(task)

            # Analyze tasks
            current_process = None
            crew_method = getattr(crew_instance, "crew", None)
            if crew_method:
                crew_obj = crew_method()
                current_process = getattr(crew_obj, "process", None)

            # Determine optimal process
            optimal_process = OrchestrationStrategy.determine_optimal_strategy(tasks)

            results[crew_class.__name__] = {
                "current_process": current_process,
                "optimal_process": optimal_process,
                "task_count": len(tasks),
                "async_tasks": sum(1 for task in tasks if getattr(task, "async_execution", False)),
            }

            # Update if requested
            if not analyze_only and process_type:
                # This would require modifying the source code, which is complex
                # For now, we'll just return the recommendation
                pass

        return results

    except Exception as e:
        logger.error(f"Error analyzing crew: {str(e)}")
        return {"error": str(e)}
