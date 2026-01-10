# Explanations

Understanding-oriented documentation explaining concepts, architecture, and design decisions.

## Architecture

| Topic | Description |
|-------|-------------|
| [Architecture Patterns](architecture.md) | CrewAI Flow patterns and design principles |
| [Deep Research](deep_research.md) | How the deep research crew works |

## Design Decisions

### Why CrewAI Flow?

Epic News uses CrewAI's Flow paradigm for multi-agent orchestration because:

- **Declarative configuration**: Agents and tasks defined in YAML
- **Natural data flow**: Context passes between tasks automatically
- **Async execution**: Parallel task execution for performance
- **Extensibility**: Easy to add new crews without modifying core logic

### Why OpenRouter?

We use OpenRouter as the LLM provider for:

- **Model flexibility**: Switch between models without code changes
- **Cost optimization**: Access to free and paid models
- **Unified API**: Consistent interface across providers

## Related Documentation

- [Tutorials](../tutorials/index.md) - Learn by doing
- [How-to Guides](../how-to/index.md) - Solve specific problems
- [Reference](../reference/index.md) - Detailed specifications
