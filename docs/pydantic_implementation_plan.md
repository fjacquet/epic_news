# Pydantic and Model Directory Refactoring Plan (Corrected)

This document outlines the corrected plan to refactor crews using a modular, test-driven approach, ensuring alignment with project conventions.

## 1. Core Principles

- **Modular Models**: Crew-specific report models will reside in `src/epic_news/models/crews/`.
- **Structured Output**: Key crews will be refactored to use `output_pydantic` in their **Python task definitions**, not in YAML.
- **Toolless Reporter Pattern**: The final task of each crew will be executed by an agent with no tools assigned.
- **Configuration-Driven**: Agent and task *definitions* will remain in YAML. The `output_pydantic` model assignment is a code-level concern.
- **Test-Driven**: The refactoring will be supported by new and existing tests.

## 2. Model Structure and Testing

The model file structure and testing plan remain the same as the previous revision. All crew-specific models will be in `src/epic_news/models/crews/` and will be tested by `tests/models/test_crew_report_models.py`.

## 3. Refactoring Process (Corrected)

For each crew, the process is:

1.  **YAML `agents.yaml`**: Ensure the final "reporter" agent is defined and has `tools: []`.
2.  **YAML `tasks.yaml`**: Ensure the final task is defined with a clear `description` and `expected_output`. **DO NOT** add `output_pydantic` here.
3.  **Python Crew File**:
    -   Import the corresponding Pydantic model from `src.epic_news.models.crews`.
    -   In the `@task` definition for the final reporting task, add the `output_pydantic=YourReportModel` parameter to the `Task()` constructor.

This approach correctly separates the configuration of the task's *intent* (in YAML) from the implementation detail of its *output structure* (in Python).

## 4. Implementation Checklist (Corrected)

The checklist in `TODO.md` will be updated to reflect this corrected, convention-aligned process.
