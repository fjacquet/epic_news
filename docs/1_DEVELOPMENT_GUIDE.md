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

## 2. CrewAI Flow: Engagement Rules & Best Practices

### 2.1. Execution Method (CRITICAL)

**ALWAYS** use the CrewAI Flow command to run crews. This is the single most important rule for maintaining a consistent and manageable architecture.

```bash
# ✅ CORRECT - Use CrewAI Flow command
crewai flow kickoff

# ❌ WRONG - Never run Python modules directly
# python -m src.epic_news.crews.fin_daily.run
# python src/epic_news/main.py
```

**Why this matters:**

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

```
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

## 6. Development Workflow

- **Package Management**: Use `uv` for all Python operations.
- **Testing**:
  - Focus on testing deterministic components (tools).
  - Use `crewai flow kickoff` for end-to-end validation.
  - Do not write unit tests for non-deterministic agents.
- **Documentation**: Update the relevant handbooks when adding new tools or patterns.
