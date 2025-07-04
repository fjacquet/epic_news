# Observability and Automatic Guardrails Guide

This guide provides comprehensive documentation for Epic News Crews' observability and monitoring system, including tracing, dashboards, and hallucination prevention.

## Overview

The observability system consists of three main components:

1. **Tracing** - Captures detailed events during crew execution
2. **Dashboard** - Visualizes performance metrics and execution patterns
3. **Hallucination Guard** - Prevents and detects AI hallucinations in outputs

All observability features are implemented in a modular, non-intrusive way using decorators and factory functions to minimize code changes when adding observability.

## Directory Structure

The observability system uses the following directory structure:

```
epic_news/
├── output/
│   ├── traces/             # Contains JSON trace files (one per execution)
│   ├── dashboard_data/     # Contains JSON metric data for dashboards
│   └── dashboards/         # Contains generated HTML dashboard files
└── templates/
    ├── dashboard_template.html  # Template for dashboard generation
    └── css/
        └── dashboard.css        # Styles for dashboard
```

## Tracing System

The tracing system captures detailed events during crew execution for debugging and performance analysis.

### Key Components

- **TraceEvent** - Represents an individual trace event with type, source, details, and timestamp
- **Tracer** - Collects and persists trace events to JSON files

### Usage

```python
from epic_news.utils.observability import Tracer, TraceEvent, trace_task

# Create a tracer for a specific execution
tracer = Tracer(trace_id="my_execution_123")

# Add events manually
tracer.add_event(TraceEvent(
    event_type="tool_call",
    source="researcher_agent",
    details={"tool_name": "web_search", "query": "latest AI news"}
))

# Use decorator to automatically trace a task
@trace_task(tracer)
def execute_research(topic):
    # Task implementation
    pass
```

### Trace File Format

Trace files are stored in JSON format with the following structure:

```json
{
  "trace_id": "trace_1623984567",
  "events": [
    {
      "event_type": "task_start",
      "source": "researcher_agent",
      "details": {"task_name": "research_task"},
      "timestamp": 1623984568.123
    },
    // More events...
  ]
}
```

## Dashboard System

The dashboard system visualizes observability data through HTML dashboards with charts and metrics.

### Key Components

- **Dashboard** - Collects and stores metrics for various system components
- **DashboardGenerator** - Generates HTML dashboards from metrics data

### Usage

```python
from epic_news.utils.observability import Dashboard, monitor_agent
from epic_news.utils.dashboard_generator import generate_all_dashboards

# Create a dashboard for monitoring
dashboard = Dashboard(dashboard_id="news_crew_run_123")

# Update metrics
dashboard.update_metric(
    category="agents",
    name="researcher",
    metric="execution_time",
    value=12.5
)

# Use decorator to automatically monitor an agent
@monitor_agent(dashboard)
def execute_agent_task(agent, task):
    # Agent execution code
    pass

# Generate dashboards from all collected metrics
generate_all_dashboards()
```

### Dashboard Data Format

Dashboard data is stored in JSON files with the following structure:

```json
{
  "crews": {
    "news_crew": {
      "execution_time": 45.2,
      "success_rate": 0.95
    }
  },
  "agents": {
    "researcher": {
      "execution_time": 12.5,
      "token_usage": 1250
    }
  },
  "tasks": { ... },
  "tools": { ... },
  "system": { ... }
}
```

## Hallucination Guard

The hallucination guard helps detect and prevent AI hallucinations in agent outputs.

### Key Components

- **HallucinationGuard** - Validates outputs against known facts and detects potential hallucinations

### Usage

```python
from epic_news.utils.observability import HallucinationGuard, guard_output

# Create a hallucination guard
guard = HallucinationGuard(
    confidence_threshold=0.7,
    fact_checking_enabled=True
)

# Add known facts
guard.add_known_fact("company_founded", "2022-05-15")
guard.add_known_fact("employee_count", 150)

# Check a statement manually
result = guard.check_statement(
    statement="The company was founded in 2020 and has 500 employees",
    context={"topic": "company profile"}
)

# Use decorator to automatically guard function outputs
@guard_output(guard, context={"source": "web_data"})
def generate_company_profile(company_data):
    # Implementation
    return profile
```

## Integrating with Crews

The observability system provides a convenient factory function to get all necessary observability tools for a crew:

```python
from epic_news.utils.observability import get_observability_tools

# In your crew class
def __init__(self):
    # Get observability tools
    observability_tools = get_observability_tools(crew_name="news_crew")
    
    # Unpack tools
    self.tracer = observability_tools["tracer"]
    self.dashboard = observability_tools["dashboard"]
    self.hallucination_guard = observability_tools["hallucination_guard"]
```

## Viewing Dashboards

Generated dashboards are available in the `output/dashboards/` directory as HTML files that can be opened in any web browser. Each dashboard provides:

1. Key Performance Metrics (runs, success rate, completion time, hallucination score)
2. System Performance visualizations
3. Agent Performance breakdowns
4. Task Execution timeline
5. Tool Usage statistics

## Best Practices

1. **Use decorators** - Apply observability through decorators rather than modifying function bodies
2. **Centralize initialization** - Use `get_observability_tools()` to get all tools for a crew
3. **Hierarchical tracing** - Create a hierarchy of trace events (crew → agent → task → tool)
4. **Balanced monitoring** - Monitor important metrics but avoid excessive data collection
5. **Regular dashboard generation** - Generate dashboards after each significant run or batch of runs

## Related Documentation

- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) - Design principles for Epic News Crews
- [tools_handbook.md](tools_handbook.md) - Guide to available tools
- [CREWAI_TOOLS_AND_MCP_GUIDE.md](CREWAI_TOOLS_AND_MCP_GUIDE.md) - Guide to CrewAI tools and MCP
