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
logger = logging.getLogger("task_orchestration")


class OrchestrationStrategy:
    """
    Defines different orchestration strategies for crews and tasks.
    """

    SEQUENTIAL = Process.sequential
    HIERARCHICAL = Process.hierarchical

    @staticmethod
    """
This module provides utilities for task orchestration, including strategy
selection and optimization for CrewAI processes.
"""

from enum import Enum
from loguru import logger
from typing import Any, Dict, List

from crewai import Process

# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class OrchestrationStrategy(Enum):
    """
    Defines the orchestration strategies for CrewAI processes.
    """

    SEQUENTIAL = Process.sequential
    HIERARCHICAL = Process.hierarchical


def select_orchestration_strategy(
    tasks: List[Any], strategy: OrchestrationStrategy = OrchestrationStrategy.SEQUENTIAL
) -> Process:
    """
    Selects the orchestration strategy for a list of tasks.

    Args:
        tasks (List[Any]): A list of tasks to be orchestrated.
        strategy (OrchestrationStrategy): The desired strategy (sequential or hierarchical).

    Returns:
        Process: The selected CrewAI process type.
    """
    logger.info(f"Selecting orchestration strategy: {strategy.name}")
    return strategy.value


def optimize_crew_process(crew_details: Dict[str, Any]) -> OrchestrationStrategy:
    """
    Analyzes crew details to recommend an optimal orchestration strategy.

    This function checks the number of async tasks and total tasks to suggest
    whether a sequential or hierarchical process would be more efficient.

    Args:
        crew_details (Dict[str, Any]): A dictionary containing details about the
                                     crew, including 'task_count' and 'async_tasks'.

    Returns:
        OrchestrationStrategy: The recommended strategy.
    """
    task_count = crew_details.get("task_count", 0)
    async_tasks = crew_details.get("async_tasks", 0)

    # If more than half of the tasks are asynchronous, recommend hierarchical
    if async_tasks > task_count / 2:
        logger.info("Recommending HIERARCHICAL strategy due to high number of async tasks.")
        return OrchestrationStrategy.HIERARCHICAL
    else:
        logger.info("Recommending SEQUENTIAL strategy.")
        return OrchestrationStrategy.SEQUENTIAL


if __name__ == "__main__":
    # Example usage of the task orchestration utilities

    # 1. Define a mock list of tasks
    mock_tasks = ["task1", "task2", "task3"]

    # 2. Select a sequential strategy
    sequential_process = select_orchestration_strategy(mock_tasks, OrchestrationStrategy.SEQUENTIAL)
    print(f"Selected process for sequential: {sequential_process}")

    # 3. Select a hierarchical strategy
    hierarchical_process = select_orchestration_strategy(mock_tasks, OrchestrationStrategy.HIERARCHICAL)
    print(f"Selected process for hierarchical: {hierarchical_process}")

    # 4. Optimize crew process based on task details
    # Scenario 1: Low number of async tasks
    crew1_details = {"task_count": 5, "async_tasks": 1}
    optimal_strategy1 = optimize_crew_process(crew1_details)
    print(f"Optimal strategy for crew 1: {optimal_strategy1.name}")

    # Scenario 2: High number of async tasks
    crew2_details = {"task_count": 5, "async_tasks": 4}
    optimal_strategy2 = optimize_crew_process(crew2_details)
    print(f"Optimal strategy for crew 2: {optimal_strategy2.name}")


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
