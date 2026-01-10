# Troubleshooting

Solutions for common problems and error messages.

## Common Issues

| Problem | Solution |
|---------|----------|
| [Common Errors](common_errors.md) | Solutions for frequently encountered errors |

## Quick Fixes

### ModuleNotFoundError

```bash
# Reinstall in editable mode
uv pip install -e .
```

### API Key Errors

1. Check `.env` file exists and contains required keys
2. Verify keys are valid and not expired
3. Ensure no trailing whitespace in key values

### CrewAI Timeout

```bash
# Increase timeout in .env
LLM_TIMEOUT_DEFAULT=600
```

## Getting Help

If you can't find a solution:

1. Check [Common Errors](common_errors.md) for detailed solutions
2. Search [GitHub Issues](https://github.com/fjacquet/epic_news/issues)
3. Create a new issue with reproduction steps

## Related Documentation

- [How-to Guides](../how-to/index.md) - Step-by-step solutions
- [Development Setup](../how-to/development_setup.md) - Environment configuration
