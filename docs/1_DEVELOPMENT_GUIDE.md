# 1. Epic News Development Guide

> **Light as a Haiku** 🌸
> Epic News is designed to be elegant, minimalist, and simple. Every line of code should serve a purpose.

## 1. Philosophy & Core Principles

Epic News operates on the **CrewAI Flow paradigm** - a revolutionary approach to multi-agent AI systems that emphasizes:

- **CrewAI-First**: Use framework capabilities before writing custom Python.
- **Configuration-Driven**: Separate code from configuration using YAML.
- **Context-Driven**: Let data flow naturally through the system.
- **Async by Default**: Maximize performance with parallel execution.

### 1.1. General Principles

- **KISS (Keep It Simple, Stupid)**: Favor simple solutions over complex ones.
- **YAGNI (You Aren't Gonna Need It)**: Don't build features until they're needed.
- **DRY (Don't Repeat Yourself)**: Eliminate code duplication through abstraction.
- **Fail Fast**: Validate inputs early and provide clear error messages. Use type hints and Pydantic models for data validation.
- **Immutable State**: State flows through the system without mutation. Use Pydantic models for structured data with clear state transitions.

### 1.2. Code Style and Quality

- **Imports**: ALL imports must be placed at the top of Python files, never inside functions or methods. This ensures clarity, prevents circular imports, and follows PEP 8 standards.
- **Whitespace**: Avoid trailing whitespace (`W291`) and whitespace on blank lines (`W293`). These are enforced by `ruff` and help maintain a clean, readable codebase.

### 1.3. Development Tools & Environment

#### Package Management

- **ALWAYS use `uv`**: Epic News exclusively uses `uv` for all Python package management operations. Never use `pip`, `poetry`, or other package managers.

```bash
# ✅ CORRECT - Use uv for all operations
uv add package-name
uv remove package-name
uv run pytest
uv run python script.py
uv sync

# ❌ WRONG - Never use other package managers
# pip install package-name
# poetry add package-name
```

**Why uv?**

- **Speed**: Significantly faster than pip/poetry
- **Reliability**: Better dependency resolution
- **Consistency**: Ensures reproducible environments
- **Modern**: Built for Python 3.10+ with latest standards

#### Logging

Epic News uses **Loguru** for all logging. It provides a more powerful and flexible logging system than the standard `logging` module.

**Configuration:**

- The main logging configuration is located in `src/epic_news/utils/logger.py`.
- By default, logs are sent to the console and to a file in the `logs/` directory.
- The `setup_logging()` function in `src/epic_news/utils/logger.py` is called at the beginning of the `kickoff` function in `src/epic_news/main.py` to configure the log sinks.

**Usage:**

- To use the logger in any module, simply import it:

  ```python
  from loguru import logger
  ```

- Then, you can use the logger to log messages at different levels:

  ```python
  logger.debug("This is a debug message.")
  logger.info("This is an info message.")
  logger.warning("This is a warning message.")
  logger.error("This is an error message.")
  logger.critical("This is a critical message.")
  ```

#### Commit Messages

Well-crafted commit messages are crucial for maintaining a clean and understandable project history. They should be clear, concise, and follow a consistent style.

##### Multiline Commit Messages

When writing multiline commit messages, avoid passing the message directly via the command line, as it can be complex and error-prone with quoting. Instead, use a temporary file.

##### Workflow

1. **Create a temporary file** with your detailed commit message.
2. **Use the `-F` or `--file` flag** with `git commit` to read the message from the file.
3. **Delete the temporary file** after the commit is successful.

##### Example

```bash
# 1. Write the commit message to a temporary file
echo "feat: Add new feature

- Detailed description of the feature.
- Rationale behind the implementation.
- Closes #123" > commit_message.tmp

# 2. Commit using the file
git commit -F commit_message.tmp

# 3. Clean up the temporary file
rm commit_message.tmp
```

This approach ensures that your commit messages are well-formatted and easy to write, especially for more complex changes.

#### Testing & Quality Assurance

- **Testing**: Always run tests with `uv run pytest`
- **Linting**: Use `ruff` for code quality (integrated with uv)
- **Type Checking**: Leverage Pydantic models and type hints
- **Coverage**: Maintain comprehensive test coverage for all utilities

#### Advanced Testing Libraries

To enhance our testing capabilities, Epic News integrates the following libraries for more robust and realistic tests:

- **`Faker`**: For generating realistic mock data (e.g., names, addresses, dates). This helps create tests that more closely resemble real-world scenarios.
- **`pytest-mock`**: A wrapper around the standard `unittest.mock` library, providing a more convenient and pytest-friendly interface for mocking objects and functions.
- **`pendulum`**: For precise control over date and time in tests. This is crucial for testing time-sensitive logic, allowing you to "freeze" time or travel to specific points in time.

##### Example Usage

```python
import pendulum
from faker import Faker

def test_faker_and_pendulum():
    """
    This test demonstrates the use of Faker and Pendulum.
    """
    fake = Faker()
    name = fake.name()
    now = pendulum.now()

    assert isinstance(name, str)
    assert isinstance(now, pendulum.DateTime)

def test_mocking_with_pytest_mock(mocker):
    """
    This test demonstrates the use of pytest-mock.
    """
    # Create a mock object
    mock_object = mocker.Mock()

    # Configure the mock to return a specific value when a method is called
    mock_object.get_name.return_value = "Test Name"

    # Call the method on the mock object
    result = mock_object.get_name()

    # Assert that the method was called and returned the expected value
    mock_object.get_name.assert_called_once()
    assert result == "Test Name"
```

#### Using `contextlib` for Cleaner Tests

To further improve the readability and maintainability of our tests, we use Python's built-in `contextlib` library to create reusable context managers for mocking dependencies. This is particularly useful when multiple tests require the same set of mocks.

##### Benefits

- **Encapsulation:** Bundles related setup and teardown logic into a single, reusable function.
- **Readability:** Replaces repetitive `mocker.patch()` calls with a clean `with` statement, making the test's intent clearer.
- **Maintainability:** Allows you to update mocking logic in one central place, rather than in every test.

##### Example

Instead of this:

```python
def test_some_function_with_many_mocks(mocker):
    mocker.patch("module.a.dependency_one")
    mocker.patch("module.b.dependency_two")
    mocker.patch("module.c.dependency_three")
    # ... test logic ...
```

We can create a reusable context manager:

```python
# In a helper file like tests/utils/context_managers.py
from contextlib import contextmanager

@contextmanager
def mock_app_dependencies(mocker):
    """A context manager to mock core application dependencies."""
    mocks = {
        "dep1": mocker.patch("module.a.dependency_one"),
        "dep2": mocker.patch("module.b.dependency_two"),
        "dep3": mocker.patch("module.c.dependency_three"),
    }
    try:
        yield mocks
    finally:
        # Teardown is handled automatically by pytest-mock
        pass

# The test becomes much cleaner:
def test_some_function_with_many_mocks(mocker):
    with mock_app_dependencies(mocker) as mocks:
        # ... test logic using mocks['dep1'], etc.
```

This approach is highly encouraged for complex test setups.

#### Development Workflow

1. Environment Setup:
   - Run `uv sync` to install dependencies
   - Install the package in editable mode: `uv pip install -e .`
   - This creates a special link to your source code and prevents import errors like `ModuleNotFoundError: No module named 'epic_news'`

2. Make Changes: Edit code, add features, fix bugs

3. Test Changes:
   - Run `uv run pytest` to ensure tests pass
   - For specific components: `uv run python tests/bin/regenerate_holiday_plan.py`

4. Quality Checks: Run `uv run yamlfix src ; uv run ruff check --fix` to ensure code quality

5. Execute Crews:
   - Use `crewai flow kickoff` to run CrewAI flows
   - This validates the complete pipeline including Pydantic model validation

## CrewAI Flow: Engagement Rules & Best Practices

### Execution Method (CRITICAL)

**ALWAYS** use the CrewAI Flow command to run crews. This is the single most important rule for maintaining a consistent and manageable architecture.

```bash
# ✅ CORRECT - Use CrewAI Flow command
crewai flow kickoff

# ❌ WRONG - Never run Python modules directly
# python -m src.epic_news.crews.fin_daily.run
# python src/epic_news/main.py
```

##### Why this matters

- CrewAI Flow manages the complete execution lifecycle.
- It ensures proper state management and context injection.
- It handles async execution and crew coordination.
- It guarantees that all crews follow the same execution pattern.

### 2.2. Anti-Patterns (What to Avoid)

- **NEVER** bypass CrewAI Flow with direct Python execution (`MyCrew().crew().kickoff()`).
- **NEVER** call crew methods directly from `main.py`.
- **NEVER** reinvent the wheel. Use existing utilities like `ensure_output_directories()` instead of `os.makedirs()`.
- **NEVER** pass context via constructor parameters. Use CrewAI's input mechanism.

```python
# ✅ CORRECT - Context-driven
crew_inputs = self.state.to_crew_inputs()
result = MyCrew().crew().kickoff(inputs=crew_inputs)

# ❌ WRONG - Constructor injection
crew = MyCrew(topic=topic, objective=objective)
```

### 2.3. Python Type Compatibility (CRITICAL)

**CrewAI Pydantic Schema Parser Limitation**: CrewAI's internal schema parser is incompatible with Python 3.10+ Union syntax (`X | Y`).

**ALWAYS** use the legacy `Union[X, Y]` or `Optional[X]` syntax for all Pydantic models used with CrewAI.

```python
from typing import Union, Optional

# ✅ CORRECT - Compatible with CrewAI
field: Union[str, None] = None
field: Optional[str] = None

# ❌ WRONG - Causes AttributeError in CrewAI
field: str | None = None
```

**Rationale**: CrewAI's `PydanticSchemaParser` attempts to access `field_type.__name__` on `types.UnionType` objects, which don't have this attribute. This causes runtime errors during schema generation for task outputs.

### 2.4. Data Normalization for Pydantic Validation

When working with external data (especially from LLMs) that needs to be validated against Pydantic models:

1. **Field Name Mapping**: Create normalization functions to map field names:

   ```python
   # Map alternative field names to expected schema names
   if "name" in source and "title" not in source:
       source["title"] = source["name"]
   if "type" in contact and "service" not in contact:
       contact["service"] = contact["type"]
   ```

2. **Multilingual Key Handling**: Handle alternative language keys:

   ```python
   # Map French keys to English
   if "numéro" in contact and "number" not in contact:
       contact["number"] = contact["numéro"]
   if "fr" in phrase and "french" not in phrase:
       phrase["french"] = phrase["fr"]
   ```

3. **Structure Conversion**: Convert data structures as needed:

   ```python
   # Convert strings to objects with required fields
   if isinstance(phrase, str):
       phrase = {"french": phrase, "local": phrase}
   ```

4. **Default Values**: Provide sensible defaults for missing required fields:

   ```python
   # Ensure required fields exist
   if "address" not in accommodation:
       accommodation["address"] = "Address not provided"
   ```

This approach ensures robust validation while maintaining flexibility with various input formats.

## 3. Agent Handbook

This section establishes the core principles, ethical standards, and research methodologies for all AI agents.

### 3.1. Agent Code of Conduct

#### Core Principles

1. **Accuracy and Thoroughness**: Always provide complete, accurate information. Cite authoritative sources and acknowledge limitations.
2. **Output Quality**: Structure information logically. Use formatting to enhance readability and follow specified output formats exactly.
3. **Ethical Guidelines**: Present balanced perspectives. Avoid biased language and respect intellectual property.
4. **Collaboration**: Pass complete context to other agents. Document reasoning and maintain a consistent tone.
5. **Technical Best Practices**: Follow project design principles (KISS, DRY). Write clean, documented, and tested code.

#### Agent Responsibilities

- **Research Agents**: Provide exhaustive, factual information (20+ data points). Use tools freely, as they do not write to the final output file.
- **Reporting Agents**: Transform research into well-structured, professional reports. **DO NOT USE TOOLS** to prevent action traces from contaminating the final HTML output.

### 3.2. Shared Research Guidelines

- **Objectivity**: Analysis must be impartial and backed by verifiable evidence.
- **Clarity**: Use clear, concise language.
- **Rigor**: Triangulate information from multiple sources.
- **Adherence**: Strictly follow task instructions and constraints.
- **Professionalism**: Format output in a clean, readable manner.

## 4. Output Standards

The primary output of each crew is a comprehensive HTML report.

### 4.1. Critical Reminders

- **DO NOT** return raw API responses.
- **DO NOT** include placeholder text like 'TODO'.
- **ALWAYS** ensure your final output is a single, complete, and well-formed HTML document.

### 4.2. HTML Report Standards

- **Structure**: Use proper HTML5 (`<!DOCTYPE html>`) with UTF-8 encoding (`<meta charset="UTF-8">`).
- **Content**: Present information in logical sections with clear headings, data sources, and actionable conclusions.
- **Prohibited**: No raw JSON, API responses, or malformed HTML.
- **Emoji Usage**: Use emojis strategically to highlight key points (e.g., 📈 for growth, ⚠️ for risks).

### 4.3. HTML Output Architecture (CRITICAL)

CrewAI has a known issue where agents with tools write action traces to output files instead of the final result. To prevent this, use a **Two-Agent Pattern**.

1. **Research Agent(s)**: Equipped with tools to gather information. They do not have an `output_file` and pass data to the next agent via context.
2. **Reporting Agent**: Has **NO TOOLS**. This agent's sole purpose is to take the data from the context and generate a clean HTML report.

```python
# ✅ CORRECT - Separate research and reporting agents
@agent
def researcher(self) -> Agent:
    return Agent(
        tools=[WikipediaSearchTool(), SerperDevTool()],  # Research with tools
    )

@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # NO TOOLS = No action traces
        # Generates clean HTML output
    )
```

## 5. Configuration & Project Structure

### 5.1. YAML-First Approach

Define agents, tasks, and crews in YAML files to separate configuration from code.

```yaml
# agents.yaml
product_researcher:
  role: "Product Research Specialist"
  goal: "Research {topic} comprehensively"
  backstory: "Expert in analyzing products and market trends"
```

### 5.2. Tool Assignment (CRITICAL)

**NEVER** specify tools in `agents.yaml`. Tools must be assigned programmatically in code using centralized factories.

```python
# ✅ CORRECT - Tools assigned in code
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=self.search_tools,  # Tools from factory functions
        verbose=True,
    )
```

**Why**: Hybrid YAML/code tool configuration causes `KeyError` when CrewAI tries to map YAML tool names to non-existent functions.

### 5.3. Path and Directory Management

- **Paths**: All file paths must be project-relative and managed programmatically to avoid nested path issues.
- **Directories**: Directory creation should be centralized using `ensure_output_directories()` at application startup. Do not use `os.makedirs` within individual crew or task logic.

### 5.4. Project Structure

```bash
epic_news/
├── src/epic_news/
│   ├── crews/           # Crew implementations
│   ├── tools/           # Tool implementations
│   ├── models/          # Pydantic models
│   └── main.py          # Flow orchestration
├── docs/                # Documentation
├── output/              # Generated reports
└── tests/               # Unit tests
```

### 4.4. Menu Designer & HTML Renderer Learnings

The following best-practices were distilled while integrating the **MenuDesignerCrew** and its HTML pipeline:

1. **Pydantic `Union` Syntax** – CrewAI’s internal schema parser still requires legacy `typing.Union` / `Optional[...]` annotations. Ensure every field in `menu_designer_report.py` (and any new model) avoids the `X | Y` pipe syntax to prevent runtime parsing errors.
2. **Factory Pattern Consistency** – Each crew must expose a small, deterministic factory (e.g. `menu_to_html`) that:
   - Normalises `CrewOutput`, Pydantic model or `dict` into a serialisable `dict`.
   - Delegates body creation to `TemplateManager.render_report()` using the correct crew identifier.
   - Optionally persists the resulting HTML.
3. **Renderer Construction** – All concrete subclasses of `BaseRenderer` **must implement `__init__`** (even if empty) to avoid Python treating them as abstract, otherwise TemplateManager fails to instantiate them.
4. **Nested Meal Rendering** – For structured meals (`starter` / `main_course` / `dessert`), `MenuRenderer` now:
   - Detects nested dicts within `lunch` / `dinner` entries.
   - Renders readable bullet-lists with appropriate emojis.
   - Falls back gracefully to plain strings when structure is missing.
5. **DailyMenu Iteration** – `MenuRenderer` supports both legacy `{day: meals}` mappings and the new list-of-objects (`DailyMenu`) produced by the Pydantic model.
6. **Debugging Pattern** – Use `dump_crewai_state()` to capture problematic crew outputs. Enable by setting `DEBUG_STATE=true` in the environment.

Adhering to these guidelines keeps new menu-style crews consistent with the broader HTML rendering architecture.

## 6. Development Workflow

- **Package Management**: Use `uv` for all Python operations.
- **Testing**:
  - Focus on testing deterministic components (tools).
  - Use `crewai flow kickoff` for end-to-end validation.
  - Do not write unit tests for non-deterministic agents.
- **Documentation**: Update the relevant handbooks when adding new tools or patterns.
