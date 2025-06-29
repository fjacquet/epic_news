# CrewAI Engagement Rules and Anti-Patterns

## Core Principles

### 1. CrewAI-First Architecture

- **ALWAYS** use `crewai flow kickoff` to run crews
- **NEVER** bypass CrewAI Flow with direct Python execution
- **NEVER** call crew methods directly from main.py
- Each crew must be a proper CrewAI crew with agents, tasks, and flow management

### 2. Proper Flow Management

- Use CrewAI Flow state management exclusively
- Pass data between crews through proper state objects
- Never bypass the flow lifecycle with custom orchestration

### 3. Don't Reinvent the Wheel

- **ALWAYS** use existing utilities like `ensure_output_directories()`
- **NEVER** reimplement directory creation with `os.makedirs()`
- **NEVER** duplicate functionality that already exists in the codebase

## Anti-Patterns and Violations

### ❌ WRONG: Bypassing CrewAI Flow

```python
# DON'T DO THIS - Direct crew instantiation and method calls
html_designer = HtmlDesignerCrew()
html_content = html_designer.render_unified_report(state_data)
```

### ✅ CORRECT: Using CrewAI Flow

```python
# DO THIS - Proper CrewAI Flow usage
@listen("go_generate_html")
def generate_html_report(self):
    inputs = self.state.to_crew_inputs()
    result = HtmlDesignerCrew().crew().kickoff(inputs=inputs)
```

### ❌ WRONG: Reinventing Directory Management

```python
# DON'T DO THIS - Manual directory creation
os.makedirs(os.path.dirname(self.state.output_file), exist_ok=True)
with open(self.state.output_file, "w", encoding="utf-8") as f:
    f.write(html_content)
```

### ✅ CORRECT: Using Existing Utilities

```python
# DO THIS - Use existing utilities
from epic_news.utils.directory_utils import ensure_output_directories
ensure_output_directories(self.state.selected_crew)
```

### ❌ WRONG: Custom Orchestration Logic

```python
# DON'T DO THIS - Manual crew coordination
def render_unified_report(self, state_data: dict[str, Any]) -> str:
    selected_crew = state_data.get("selected_crew", "UNKNOWN")
    self.output_file_path = determine_output_path(selected_crew, state_data)
    # ... custom logic bypassing CrewAI
```

### ✅ CORRECT: CrewAI Agent-Task Architecture

```python
# DO THIS - Proper agent and task definitions
@agent
def html_designer_agent(self) -> Agent:
    return Agent(
        role="HTML Report Designer",
        goal="Generate professional HTML reports",
        backstory="Expert in HTML generation and report formatting"
    )

@task
def generate_html_task(self) -> Task:
    return Task(
        description="Generate HTML report from structured data",
        agent=self.html_designer_agent,
        expected_output="Valid HTML report file"
    )
```

## Enforcement Rules

1. **Code Review Checklist:**
   - [ ] No direct crew method calls from main.py
   - [ ] All crews use proper CrewAI Flow lifecycle
   - [ ] No reimplementation of existing utilities
   - [ ] Proper state management through CrewAI Flow

2. **Testing Requirements:**
   - All crews must be testable through `crewai flow kickoff`
   - No unit tests that bypass CrewAI Flow architecture
   - Integration tests must use proper flow state management

3. **Documentation Standards:**
   - Document all crew interactions through flow diagrams
   - Explain state transitions between crews
   - Provide examples of proper CrewAI usage patterns

## Lessons Learned

### Recent Violations Fixed

1. **HtmlDesignerCrew Bypass**: Was calling `render_unified_report()` directly instead of using CrewAI agents/tasks
2. **Directory Management**: Was using `os.makedirs()` instead of `ensure_output_directories()`
3. **State Management**: Was setting invalid fields on CrewAI Flow state objects
4. **Flow Lifecycle**: Was bypassing proper crew kickoff mechanisms

### Key Takeaways

- CrewAI Flow is not optional - it's the foundation of the architecture
- Every crew must have proper agents, tasks, and flow integration
- Utilities exist for a reason - use them instead of reinventing
- State management must follow CrewAI patterns, not custom solutions

## Future Compliance

All future development must:

1. Start with CrewAI Flow design
2. Use existing utilities and patterns
3. Follow proper agent-task architecture
4. Maintain state through CrewAI mechanisms
5. Test through `crewai flow kickoff` exclusively

**Remember: Be smart, be brave, and follow the rules. CrewAI-First, always.**
