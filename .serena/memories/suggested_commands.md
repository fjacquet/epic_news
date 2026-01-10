# Suggested Commands for Epic News

## Essential Commands

### Package Management (ALWAYS use `uv`)
```bash
# Install dependencies
uv sync

# Install package in editable mode (prevents ModuleNotFoundError)
uv pip install -e .

# Add a new package
uv add package-name

# Remove a package
uv remove package-name
```

### Running the Application
```bash
# Main command to run CrewAI Flow (ALWAYS use this)
crewai flow kickoff

# Alternative entry points (via project.scripts)
uv run kickoff
uv run plot
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/path/to/test_file.py

# Run tests quietly (less verbose)
uv run pytest -q

# Run specific PR tests (e.g., PR-001)
uv run pytest -q tests/tools/test_json_outputs.py tests/tools/test_http_resilience.py
```

### Code Quality & Linting
```bash
# Run ruff linter (check for issues)
uv run ruff check .

# Run ruff linter with auto-fix
uv run ruff check --fix .

# Run ruff formatter
uv run ruff format .

# Combined: format and lint
uv run yamlfix src ; uv run ruff check --fix
```

### YAML Linting
```bash
# Run yamllint
uv run yamllint -s .

# Fix YAML files
uv run yamlfix src
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### Git Operations
```bash
# Common git commands (macOS/Darwin compatible)
git status
git add .
git commit -F commit_message.tmp  # Use file for multiline messages
git push
git pull
git log --oneline -10

# Create branch
git checkout -b feature/branch-name

# View diff
git diff
git diff --staged
```

## macOS/Darwin-Specific Commands

### System Dependencies (WeasyPrint for PDF generation)
```bash
# Install system dependencies using Homebrew
brew install pango cairo libffi gdk-pixbuf fontconfig
```

### Standard Unix Commands (Darwin compatible)
```bash
ls -la                  # List files with details
find . -name "*.py"     # Find Python files
grep -r "pattern" .     # Search for pattern recursively
cd /path/to/directory   # Change directory
pwd                     # Print working directory
cat filename            # View file contents
tail -f logs/app.log    # Follow log file
```

## Development Workflow

1. **Setup**: `uv sync && uv pip install -e .`
2. **Make Changes**: Edit code
3. **Test**: `uv run pytest`
4. **Quality Check**: `uv run ruff check --fix`
5. **Run Flow**: `crewai flow kickoff`
6. **Commit**: Use file-based commit messages for multiline commits

## Important Notes

- **NEVER** use `pip`, `poetry`, or other package managers - ONLY use `uv`
- **NEVER** run crews directly via Python (`python -m src.epic_news.crews...`)
- **ALWAYS** use `crewai flow kickoff` to run the application
- On Darwin (macOS), all standard Unix commands work as expected
