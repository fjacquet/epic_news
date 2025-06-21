# epic_news Design Principles

## 4. Centralized Path Management

To maintain a single source of truth and prevent path-related errors, all file paths—especially for task inputs and outputs—must be defined and managed programmatically within the crew's Python source code (e.g., `your_crew.py`).

- **DO NOT** define `output_file` or other file paths in YAML configuration files (`agents.yaml`, `tasks.yaml`).
- **DO** use `os.path.join` and `os.path.abspath` to construct project-relative paths dynamically. This ensures that the application is not dependent on a specific system directory structure and that paths resolve correctly regardless of where the script is executed.
- **CRITICAL**: **NEVER** create nested `/Users/.../Users/...` directory structures. All output files must be written to the project's `/output` directory only.
- **ENFORCE**: All output files must use paths relative to the project root (e.g., `/output/news/`, `/output/logs/`) and never absolute paths that duplicate user directory structures.
- **VALIDATION**: Before writing any file, validate that the output path does not contain nested user directories or duplicate path segments.

- **Example**:

  ```python
  # In your_crew.py - CORRECT path calculation
  _crew_path = pathlib.Path(__file__).parent
  project_root = _crew_path.parent.parent.parent.parent.parent  # Calculate to project root
  output_dir = str(project_root / 'output' / 'news')  # Results in /project/output/news
  
  # WRONG - would create nested paths
  # output_dir = os.path.join(os.getcwd(), 'output', 'news')
  
  # In a task definition
  output_file = os.path.join(self.output_dir, 'report.html')
  return Task(
      config=task_config,
      output_file=output_file
  )
  ```


## Overview

epic_news is designed to be elegant and minimalist, like a haiku.
It works with crewai as a flow of tasks and as the fondation of all.
This document outlines the core principles that guide its development.

## Core Principles

> **CrewAI before Python**  
> Whenever a capability exists in the CrewAI framework, use it first before writing custom Python. Extend, don’t reinvent.

### Simple and Easy to Understand

- Code should be self-explanatory
- Functions should have a single responsibility
- Class and function names should clearly describe their purpose
- Comments and docstrings should explain "why" not just "what"

### Light as a Haiku

Like a haiku poem with its strict form of simplicity and elegance:

- Minimal dependencies
- Concise implementations
- Elegant solutions over complex ones
- Purposeful design choices

### CrewAI Flow Design Principles

- **Leverage CrewAI Core Functionality**: Adhere to and utilize the built-in mechanisms and patterns provided by the CrewAI framework. Avoid reimplementing or circumventing core framework features, focusing instead on building upon its established capabilities. This includes the principle: *Framework before Python—do not reinvent CrewAI framework*.
- **Clear Separation of Concerns**: Maintain a clear distinction between state and behavior.
- **Explicit Flow Transitions**: Define transitions between crews and tasks clearly.
- **Asynchronous by Default (where possible)**:
  - Leverage asynchronous execution (`async_execution=True`) for I/O-bound tasks to maximize performance.
  - Be mindful of framework constraints, such as the requirement for the final task in a sequential process to be synchronous.
- **Event-Driven Architecture**: Design components to react to events where applicable.

### Configuration-Driven Design

- Separate code from configuration using YAML files
- Use CrewAI decorators (@agent, @task, @crew) with config dictionaries
- Maintain strict separation between agent/task definitions and their parameters
- Configuration should be externally modifiable without code changes
- Default to configuration-driven approach, with coded fallbacks for robustness

### KISS (Keep It Simple, Stupid)

- Avoid premature optimization
- Choose straightforward solutions over clever ones
- Minimize complexity in algorithms and structures
- Favor readability over brevity

### YAGNI (You Aren't Gonna Need It)

- Only implement features that are immediately necessary
- Avoid speculative generality
- Refactor when patterns emerge, not before
- Focus on solving the current problem well

### DRY (Don't Repeat Yourself)

- Extract common functionality into helper methods
- Use inheritance and composition appropriately
- Maintain a single source of truth for data
- Leverage patterns like the template method when appropriate
- Leverage centralized project utilities, such as the common logging setup, to avoid redundant configurations and ensure consistency.

## Code Structure Guidelines

1. **Pydantic Usage**
   - Always use Pydantic V2 style validators with `@field_validator` instead of deprecated `@validator`
   - Use `ConfigDict` instead of class-based config (e.g., `model_config = ConfigDict(extra="forbid")` instead of inner `Config` class)
   - Follow Pydantic V2 best practices for all models to avoid deprecation warnings
   - Ensure all validation logic is explicit and well-documented

2. **State Management**
   - Keep state immutable where possible
   - Document state transitions clearly
   - Minimize global state

3. **Flow Design**
   - Use descriptive names for flow steps
   - Document dependencies between steps
   - Keep flows linear where possible

4. **Error Handling**
   - Fail fast and explicitly
   - Provide meaningful error messages
   - Handle edge cases gracefully

5. **Documentation**
   - Maintain a clear and consistent documentation structure. For instance, core agent guidelines reside in `agent_handbook.md`, while detailed tool specifications (including arguments, API key needs, and usage notes) are consolidated in a dedicated, alphabetically-sorted `tools_handbook.md`, with clear cross-linking.
   - Tool documentation within `tools_handbook.md` should follow a standardized format for clarity and ease of use.

6. **Tool Organization**
   - **Standardized Tool Outputs**: Tools should return data in a consistent, structured, and easily parsable format, preferably JSON strings, from their `_run` methods to ensure interoperability and predictable handling by agents.
   - **Modular Tool Design**: Favor creating focused, single-purpose tool files (e.g., one class per file, or very closely related small helper tools grouped logically). This enhances clarity, testability, and maintainability, aligning with the 'Single Responsibility Principle'.
   - **API Key Management**: Consistently use environment variables for API keys (e.g., `SERPER_API_KEY = os.getenv('SERPER_API_KEY')`). Avoid hardcoding keys and ensure clear documentation in `tools_handbook.md` if a specific key is required by a tool.
   - **Tool Testing**: All tools must have corresponding unit tests in the `tests/tools/` directory (or `tests/bin/` for scripts in `src/epic_news/bin/`). Tests should cover primary functionality, edge cases, and error handling to ensure reliability and maintainability.
   - **Tool Imports**: Always use the correct import path for CrewAI tool classes. For custom tools, use `from crewai.tools import BaseTool` (not from `crewai_tools`). This is a common source of errors and should be consistently applied across the codebase.
   - Document public interfaces thoroughly
   - Include examples where appropriate
   - Keep documentation up-to-date with code changes

7. **Module Organization**
   - Split utility functions into separate modules by functionality
   - Use empty `__init__.py` files for package structure
   - Prefer explicit imports from specific modules over package-level imports
   - Place all imports at the top of the file, never inline within functions or methods
   - Group related functionality in dedicated directories
   - **Script Organization**: Standalone operational Python scripts (e.g., data updaters, maintenance tasks) that are not direct CrewAI tools should be placed in the `src/epic_news/bin/` directory. Their tests should reside in `tests/bin/`.

8. **Project Directory Layout**
   - The `src` directory should contain only Python source code (e.g., the main application package `epic_news`, tools, etc.).
   - Data files, logs, outputs, archives, and other runtime artifacts should be stored in directories at the project root (e.g., `knowledge/`, `logs/`, `output/`, `archive/`, `storage/`).
   - Configuration in `settings.py` should define the paths to these root-level artifact directories. This keeps the source code separate from generated data and improves clarity.

9. **Python Package and Workflow Management**
   - Use `uv` for all Python package and virtual environment operations (e.g., `uv pip install`, `uv venv`).
   - Run individual Python scripts using `uv run python <script.py>`.
   - To execute the main project workflow, use the `crewai flow kickoff` command from the project root. This is the standard way to run the entire sequence of crews.

10. **Report Generation**

- Generate reports in HTML format for rich presentation
- Always include UTF-8 encoding declarations to handle special characters and emojis
- Use emojis strategically to enhance readability and visual appeal
- Ensure cross-browser compatibility with proper HTML5 standards
- Structure reports with clear sections and a logical flow of information

1. **Pydantic Model Organization**
    - **Separation of Concerns**: Pydantic models (schemas) used by tools must be defined in separate files within the `src/epic_news/models` directory, not within the tool files themselves.
    - **Grouping**: Group related models into a single file (e.g., `github_models.py` for all GitHub-related schemas, `report_models.py` for all report-generation schemas).
    - **Imports**: Tool files should import their required models from the appropriate module in `src/epic_news/models`.
    - **Rationale**: This practice enforces a clear separation between the data structures (models) and the business logic (tools), improving modularity, reusability, and maintainability. It also keeps tool files cleaner and more focused on their specific tasks.

    ```python
    # src/epic_news/models/github_models.py - CORRECT
    from pydantic import BaseModel, Field

    class GitHubSearchInput(BaseModel):
        query: str = Field(..., description="Search query")
        # ... other fields

    # src/epic_news/tools/github_search_tool.py - CORRECT
    from crewai.tools import BaseTool
    from src.epic_news.models.github_models import GitHubSearchInput

    class GitHubSearchTool(BaseTool):
        name: str = "GitHub Search"
        args_schema: type[BaseModel] = GitHubSearchInput
        # ... implementation
    ```

```bash
crewai flow kickoff
```

- Maintain consistent package versions across development environments.

## Implementation Examples

### Good Example - DRY Principle

```python
# Instead of repeating file processing logic:
def _process_files(self, file_list: List[str], file_type: str) -> None:
    """Process files of a specific type."""
    print(f"Indexing {file_type}")
    for file in file_list:
        print(Path(file).name)
        archive_files(file)

# Then use it in specific handlers:
def index_text(self):
    self._process_files(self.state.document_state.list_txt, "text")
```

### Good Example - KISS Principle

```python
# Simple, direct approach to file archiving
def archive_files(file: str) -> None:
    """Move processed files to an archive directory."""
    knowledge_dir = "knowledge"
    archive_dir = "archive"
    
    if not os.path.exists(knowledge_dir):
        return
        
    rel_path = os.path.relpath(file, knowledge_dir)
    dest_dir = os.path.join(archive_dir, os.path.dirname(rel_path))
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_file = os.path.join(archive_dir, rel_path)
    shutil.move(file, dest_file)
```

### Good Example - Module Organization with Tool Factories

This project organizes tools by domain and uses factory functions to provide them to the crews. This keeps the crew definitions clean and separates tool implementation from tool consumption.

```text
src/epic_news/tools/
├── __init__.py
├── finance_tools.py              # Factory functions for finance tools
├── web_tools.py                  # Factory functions for web/search tools
├── coinmarketcap_info_tool.py    # Individual tool implementation example
└── serper_email_search_tool.py   # Individual tool implementation example
└── ... other individual tool files ...
```

```python
# In a crew file (e.g., src/epic_news/crews/stock_crew/stock_crew.py)

# Import the factory function, not the individual tools
from epic_news.tools.finance_tools import get_stock_research_tools
from epic_news.tools.web_tools import get_search_tools, get_scrape_tools

# The crew can then easily be equipped with a curated set of tools
class StockCrew:
    def __init__(self):
        self.tools = [
            *get_search_tools(),
            *get_scrape_tools(),
            *get_stock_research_tools(),
        ]
        # ... setup agents and tasks with these tools
```

### Good Example - Focused Tool Modules (KISS and "Light as a Haiku")

Following the principle of single responsibility and keeping modules focused, individual tools are generally placed in their own files. This enhances clarity, testability, and maintainability.

```python
# src/epic_news/tools/coinmarketcap_info_tool.py

from crewai_tools import BaseTool

# A single, focused tool in its own file.
class CoinMarketCapInfoTool(BaseTool):
    name: str = "CoinMarketCap Info Tool"
    description: str = "Fetches information for specific cryptocurrencies from CoinMarketCap."
    # ... implementation

# This promotes clarity, testability, and adherence to the Single Responsibility Principle.
# Factory functions in files like `finance_tools.py` or `web_tools.py` can then aggregate these individual tools.
```

### Good Example - HTML Report Generation with Emojis

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PowerFlex Analysis Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .emoji-header {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .key-point {
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 10px 15px;
            margin: 15px 0;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>🔍 PowerFlex Analysis Report</h1>
    <p><strong>Date:</strong> June 9, 2025</p>
    
    <div class="toc">
        <h2>📋 Table of Contents</h2>
        <ul>
            <li><a href="#summary">📊 Executive Summary</a></li>
            <li><a href="#benefits">🌟 Key Benefits</a></li>
            <li><a href="#use-cases">🛠️ Proven Use Cases</a></li>
            <li><a href="#conclusion">🏁 Conclusion</a></li>
        </ul>
    </div>
    
    <section id="summary">
        <h2><span class="emoji-header">📊</span>Executive Summary</h2>
        <p>This report addresses the question: <strong>"What are the top 5 reasons to buy PowerFlex? What are the proven benefits and use cases?"</strong></p>
        <!-- Report content continues... -->
    </section>
</body>
</html>
