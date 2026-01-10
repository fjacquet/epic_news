# Task Completion Checklist

When a task is completed, follow this checklist to ensure code quality and consistency:

## 1. Code Quality Checks

### Run Tests
```bash
# Run all tests
uv run pytest

# For specific changes, run relevant test files
uv run pytest tests/path/to/relevant_test.py

# Check coverage if adding new functionality
uv run pytest --cov
```

**Expected Outcome**: All tests pass ✅

### Run Linter
```bash
# Check for issues and auto-fix
uv run ruff check --fix .
```

**Expected Outcome**: No linting errors ✅

### Run Formatter
```bash
# Format all Python files
uv run ruff format .
```

**Expected Outcome**: All files properly formatted ✅

### YAML Validation (if YAML files were modified)
```bash
# Lint YAML files
uv run yamllint -s .

# Auto-fix YAML formatting
uv run yamlfix src
```

**Expected Outcome**: All YAML files valid ✅

## 2. Pre-commit Validation

### Run Pre-commit Hooks
```bash
# Run all pre-commit hooks on changed files
pre-commit run

# Or run on all files to be thorough
pre-commit run --all-files
```

**Expected Outcome**: All hooks pass ✅

This will automatically run:
- `ruff check --fix`
- `ruff format`
- `yamllint -s`

## 3. End-to-End Validation

### Test with CrewAI Flow
```bash
# Run the application to ensure no runtime errors
crewai flow kickoff
```

**Expected Outcome**: Application runs without errors ✅

**Note**: This is especially important when:
- Adding new crews
- Modifying Pydantic models
- Changing agent/task configurations
- Updating tool implementations

## 4. Code Review Checklist

### Self-Review
Before committing, review your changes:

- [ ] All imports are at the top of files
- [ ] No trailing whitespace (W291, W293)
- [ ] Type hints use legacy Union syntax for Pydantic models (`Union[X, Y]` not `X | Y`)
- [ ] No hard-coded paths (use project-relative paths)
- [ ] Tools assigned in code, not in YAML
- [ ] HTML rendering uses `attrs` dictionary for class attributes
- [ ] CSS uses variables with fallbacks for colors
- [ ] Empty state handling for renderers
- [ ] Logging uses `loguru.logger` not `print()` or `logging`
- [ ] No unnecessary complexity or over-engineering
- [ ] Code follows DRY, KISS, and YAGNI principles

### Documentation
- [ ] Updated relevant documentation if behavior changed
- [ ] Added docstrings for new public functions/classes (if appropriate)
- [ ] Comments added only where logic isn't self-evident

### Testing
- [ ] Tests added for new deterministic functionality (tools, utilities)
- [ ] Tests use `pytest-mock` for mocking
- [ ] Tests use `Faker` for realistic test data where appropriate
- [ ] Tests use `pendulum` for date/time control where appropriate

## 5. Git Operations

### Stage Changes
```bash
# Review what changed
git status
git diff

# Stage relevant files
git add <files>

# Or stage all changes
git add .
```

### Commit Changes
```bash
# For simple single-line commits
git commit -m "feat: descriptive message"

# For multiline commits (RECOMMENDED)
echo "feat: Add new feature

- Detailed point 1
- Detailed point 2
- Closes #123" > commit_message.tmp

git commit -F commit_message.tmp
rm commit_message.tmp
```

**Commit Message Guidelines**:
- Use conventional commits format: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, etc.
- First line: concise summary (50 chars or less)
- Body: detailed explanation if needed
- Reference related issues/PRs

### Pre-push Checklist
- [ ] All tests passing
- [ ] No linting errors
- [ ] Pre-commit hooks pass
- [ ] Application runs via `crewai flow kickoff`
- [ ] Commit messages are clear and descriptive

### Push Changes
```bash
# Push to remote
git push

# Or if new branch
git push -u origin branch-name
```

## 6. Optional: Coverage Check

If adding significant new functionality:

```bash
# Generate coverage report
uv run pytest --cov --cov-report=html

# View report (opens in browser)
open htmlcov/index.html  # macOS
```

**Target**: Aim for high coverage on utility functions and tools

## 7. Cleanup

### Remove Temporary Files
- Remove debug files
- Remove temporary test data
- Clean up any generated artifacts not meant for version control

### Verify .gitignore
Ensure the following are NOT committed:
- `.env` (contains secrets)
- `__pycache__/` directories
- `.pytest_cache/`
- `htmlcov/` (coverage reports)
- `logs/` (log files)
- `cache/` (cached data)
- Local development artifacts

## Quick Checklist Summary

For quick reference, run these commands in order:

```bash
# 1. Test
uv run pytest

# 2. Format & Lint
uv run yamlfix src ; uv run ruff check --fix

# 3. Pre-commit
pre-commit run --all-files

# 4. End-to-end validation (if appropriate)
crewai flow kickoff

# 5. Commit
git add .
git commit -F commit_message.tmp
git push
```

## Notes

- **Fail Fast**: If any step fails, fix it before proceeding
- **No Shortcuts**: Don't skip quality checks - they catch bugs early
- **Consistency**: Following this checklist ensures consistent code quality across the project
- **Automation**: Many of these checks run automatically via pre-commit hooks
