#!/usr/bin/env python
"""
Crew Optimization Script

This script analyzes and optimizes crews for better task orchestration.
It identifies crews that would benefit from parallel execution and provides
recommendations for process type changes.
"""

import argparse
import importlib
import inspect
import logging
import os
import sys
from typing import Any

from tabulate import tabulate

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from epic_news.utils.task_orchestration import OrchestrationStrategy

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("optimize_crews")

def discover_crews() -> list[str]:
    """
    Discover all crew modules in the project.

    Returns:
        List[str]: List of crew module paths
    """
    crews_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../crews"))
    crew_modules = []

    for crew_dir in os.listdir(crews_dir):
        crew_path = os.path.join(crews_dir, crew_dir)
        if os.path.isdir(crew_path):
            crew_file = os.path.join(crew_path, f"{crew_dir}_crew.py")
            if os.path.exists(crew_file):
                module_path = f"epic_news.crews.{crew_dir}.{crew_dir}_crew"
                crew_modules.append(module_path)

    return crew_modules

def analyze_all_crews() -> dict[str, dict[str, Any]]:
    """
    Analyze all crews in the project.

    Returns:
        Dict[str, Dict[str, Any]]: Analysis results for each crew
    """

    crew_modules = discover_crews()
    results = {}

    for module_path in crew_modules:
        try:
            logger.info(f"Analyzing crew module: {module_path}")
            # Analyze the crew directly without using optimize_crew_process
            module_results = analyze_crew_module(module_path)
            if module_results:
                results[module_path] = module_results
        except Exception as e:
            logger.error(f"Exception analyzing {module_path}: {str(e)}")

    return results


def analyze_crew_module(module_path: str) -> dict[str, Any]:
    """
    Analyze a crew module directly without using optimize_crew_process.

    Args:
        module_path: Path to the crew module

    Returns:
        Dict[str, Any]: Analysis results for the crew
    """
    from crewai import Process

    try:
        # Import the module
        module = importlib.import_module(module_path)

        # Find crew classes and methods
        results = {}

        for _, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                # Look for crew method in the class
                for method_name, method in inspect.getmembers(obj):
                    if method_name == 'crew' and callable(method):
                        # This is likely a crew class
                        try:
                            # Try to instantiate the class
                            instance = obj()

                            # Get the crew object
                            crew_obj = instance.crew()

                            # Get the process type
                            process_type = getattr(crew_obj, 'process', None)
                            process_name = "Unknown"
                            if process_type == Process.sequential:
                                process_name = "Sequential"
                            elif process_type == Process.hierarchical:
                                process_name = "Hierarchical"

                            # Count tasks and async tasks
                            task_count = 0
                            async_tasks = 0

                            # Look for task methods
                            for task_name, task_method in inspect.getmembers(instance):
                                if task_name.endswith('_task') and callable(task_method):
                                    try:
                                        task_obj = task_method()
                                        task_count += 1
                                        if getattr(task_obj, 'async_execution', False):
                                            async_tasks += 1
                                    except Exception:
                                        pass

                            # Determine optimal process type
                            optimal_process = "Sequential"
                            if async_tasks > task_count / 2:
                                optimal_process = "Hierarchical"

                            results[obj.__name__] = {
                                "current_process": process_name,
                                "optimal_process": optimal_process,
                                "task_count": task_count,
                                "async_tasks": async_tasks,
                            }
                        except Exception as e:
                            logger.warning(f"Error analyzing {obj.__name__}: {str(e)}")

        return results

    except Exception as e:
        logger.error(f"Error importing module {module_path}: {str(e)}")
        return {}

def display_results(results: dict[str, dict[str, Any]]) -> None:
    """
    Display analysis results in a tabular format.

    Args:
        results: Analysis results for each crew
    """
    table_data = []

    for module_path, crew_results in results.items():
        for crew_name, analysis in crew_results.items():
            current = analysis.get("current_process", "Unknown")
            if current == OrchestrationStrategy.SEQUENTIAL:
                current = "Sequential"
            elif current == OrchestrationStrategy.HIERARCHICAL:
                current = "Hierarchical"

            optimal = analysis.get("optimal_process", "Unknown")
            if optimal == OrchestrationStrategy.SEQUENTIAL:
                optimal = "Sequential"
            elif optimal == OrchestrationStrategy.HIERARCHICAL:
                optimal = "Hierarchical"

            needs_change = current != optimal and current != "Unknown"

            table_data.append([
                module_path.split(".")[-2],  # Crew name
                crew_name,
                current,
                optimal,
                analysis.get("task_count", 0),
                analysis.get("async_tasks", 0),
                "✓" if needs_change else ""
            ])

    headers = ["Crew", "Class", "Current Process", "Optimal Process",
               "Tasks", "Async Tasks", "Needs Change"]

    print("\nCrew Orchestration Analysis")
    print("==========================\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("\n")

    # Count crews that need changes
    needs_change_count = sum(1 for row in table_data if row[-1] == "✓")
    print(f"Found {needs_change_count} crews that would benefit from process type changes.")

def main():
    """Main function to run the optimization script."""
    parser = argparse.ArgumentParser(description="Analyze and optimize crews for better task orchestration")
    parser.add_argument("--apply", action="store_true", help="Apply recommended changes")
    args = parser.parse_args()

    print("Analyzing crews for optimal task orchestration...")
    results = analyze_all_crews()
    display_results(results)

    if args.apply:
        print("\nThis feature is not yet implemented. For now, please apply changes manually.")

if __name__ == "__main__":
    main()
