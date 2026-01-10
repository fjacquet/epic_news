# Epic News - Comprehensive Makefile
# Package manager: uv (exclusively)
# Documentation: Run 'make help' to see all available targets

.PHONY: help install dev build clean test coverage lint format fix \
        pre-commit security type-check \
        docker-build-api docker-build-streamlit docker-build-combined \
        docker-build-code-interpreter docker-build-all \
        run-streamlit run-api run-crew update-kb \
        clean-pyc clean-test clean-build clean-all \
        show-deps show-outdated sync lock validate ci-checks all

.DEFAULT_GOAL := help

# Configuration
PYTHON := uv run python
PYTEST := uv run pytest
RUFF := uv run ruff
YAMLLINT := uv run yamllint
YAMLFIX := uv run yamlfix
DOCKER := docker
PROJECT_NAME := epic_news
SRC_DIR := src/epic_news
TEST_DIR := tests
DOCS_DIR := docs

# Colors for help output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

##@ General

help: ## Show this help message
	@echo '$(BLUE)═══════════════════════════════════════════════════════════$(RESET)'
	@echo '$(GREEN)  Epic News - Development Makefile$(RESET)'
	@echo '$(BLUE)═══════════════════════════════════════════════════════════$(RESET)'
	@echo ''
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ''
	@echo '$(BLUE)═══════════════════════════════════════════════════════════$(RESET)'

##@ Installation & Setup

install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(RESET)"
	uv sync --locked
	uv pip install -e .
	@echo "$(GREEN)✓ Production dependencies installed$(RESET)"

dev: ## Install development dependencies (includes mypy, bandit, safety)
	@echo "$(GREEN)Installing development dependencies...$(RESET)"
	uv sync --all-extras --locked
	uv pip install -e .
	@echo "$(GREEN)Installing pre-commit hooks...$(RESET)"
	uv run pre-commit install
	@echo "$(GREEN)✓ Development environment ready$(RESET)"

build: ## Build the package distribution
	@echo "$(GREEN)Building package...$(RESET)"
	uv build
	@echo "$(GREEN)✓ Package built in dist/$(RESET)"

##@ Code Quality

test: ## Run tests quickly (no coverage)
	@echo "$(GREEN)Running tests...$(RESET)"
	$(PYTEST) -q

coverage: ## Run tests with coverage report (HTML + terminal)
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	@./bin/run_tests_with_coverage.sh

test-verbose: ## Run tests with verbose output
	@echo "$(GREEN)Running tests (verbose)...$(RESET)"
	$(PYTEST) -v

lint: ## Check code style (ruff + yamllint)
	@echo "$(GREEN)Linting Python code...$(RESET)"
	$(RUFF) check .
	@echo "$(GREEN)Linting YAML files...$(RESET)"
	$(YAMLLINT) -s src/epic_news/crews/*/config/*.yaml

format: ## Format code (ruff format + yamlfix)
	@echo "$(GREEN)Formatting Python code...$(RESET)"
	$(RUFF) format .
	@echo "$(GREEN)Formatting YAML files...$(RESET)"
	$(YAMLFIX) src/epic_news/crews/
	@echo "$(GREEN)✓ Code formatted$(RESET)"

fix: format ## Auto-fix linting issues (format + ruff --fix)
	@echo "$(GREEN)Auto-fixing linting issues...$(RESET)"
	$(RUFF) check --fix .
	@echo "$(GREEN)✓ Linting issues fixed$(RESET)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(GREEN)Running pre-commit hooks...$(RESET)"
	uv run pre-commit run --all-files

##@ Advanced Quality Checks

type-check: ## Run type checking with mypy (requires mypy in dev deps)
	@if uv run python -c "import mypy" 2>/dev/null; then \
		echo "$(GREEN)Running mypy type checks...$(RESET)"; \
		uv run mypy $(SRC_DIR); \
	else \
		echo "$(YELLOW)⚠ mypy not installed. Install with: uv add --dev mypy$(RESET)"; \
		exit 1; \
	fi

security: ## Run security checks (bandit + safety)
	@echo "$(GREEN)Checking for security issues in code...$(RESET)"
	@if uv run python -c "import bandit" 2>/dev/null; then \
		uv run bandit -r $(SRC_DIR) -f json -o bandit-report.json || true; \
		uv run bandit -r $(SRC_DIR); \
	else \
		echo "$(YELLOW)⚠ bandit not installed. Install with: uv add --dev bandit$(RESET)"; \
	fi
	@echo ""
	@echo "$(GREEN)Checking for vulnerable dependencies...$(RESET)"
	@if uv run python -c "import safety" 2>/dev/null; then \
		uv run safety check --json > safety-report.json || true; \
		uv run safety check; \
	else \
		echo "$(YELLOW)⚠ safety not installed. Install with: uv add --dev safety$(RESET)"; \
	fi

validate: lint test ## Quick validation (lint + test)
	@echo "$(GREEN)✓ Validation complete$(RESET)"

ci-checks: lint test ## Run all CI checks (lint + test)
	@echo "$(GREEN)✓ CI checks complete$(RESET)"

all: clean install lint test ## Full clean build (clean + install + lint + test)
	@echo "$(GREEN)✓ Full build complete$(RESET)"

##@ Docker Operations

docker-build-api: ## Build FastAPI Docker image
	@echo "$(GREEN)Building FastAPI image...$(RESET)"
	$(DOCKER) build -f Dockerfile.api -t $(PROJECT_NAME)-api:latest .

docker-build-streamlit: ## Build Streamlit Docker image
	@echo "$(GREEN)Building Streamlit image...$(RESET)"
	$(DOCKER) build -f Dockerfile.streamlit -t $(PROJECT_NAME)-streamlit:latest .

docker-build-combined: ## Build combined Docker image
	@echo "$(GREEN)Building combined image...$(RESET)"
	$(DOCKER) build -f Dockerfile.combined -t $(PROJECT_NAME)-combined:latest .

docker-build-code-interpreter: ## Build code interpreter Docker image
	@echo "$(GREEN)Building code interpreter image...$(RESET)"
	$(DOCKER) build -f Dockerfile.code-interpreter -t $(PROJECT_NAME)-code-interpreter:latest .

docker-build-all: docker-build-api docker-build-streamlit docker-build-combined docker-build-code-interpreter ## Build all Docker images
	@echo "$(GREEN)✓ All Docker images built$(RESET)"

docker-run-api: ## Run FastAPI container (port 8000)
	@echo "$(GREEN)Starting FastAPI container...$(RESET)"
	$(DOCKER) run -p 8000:8000 --env-file .env $(PROJECT_NAME)-api:latest

docker-run-streamlit: ## Run Streamlit container (port 8501)
	@echo "$(GREEN)Starting Streamlit container...$(RESET)"
	$(DOCKER) run -p 8501:8501 --env-file .env $(PROJECT_NAME)-streamlit:latest

docker-run-combined: ## Run combined container (ports 8000, 8501)
	@echo "$(GREEN)Starting combined container...$(RESET)"
	$(DOCKER) run -p 8000:8000 -p 8501:8501 --env-file .env $(PROJECT_NAME)-combined:latest

##@ Application Runtime

run-streamlit: ## Start Streamlit app (port 8501)
	@./bin/start_streamlit.sh

run-api: ## Start FastAPI server (port 8000)
	@./bin/start_uvicorn.sh

run-crew: ## Run CrewAI flow kickoff
	@echo "$(GREEN)Running CrewAI flow...$(RESET)"
	@export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$$DYLD_LIBRARY_PATH" && \
	export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$$PKG_CONFIG_PATH" && \
	crewai flow kickoff

plot: ## Generate crew plot/diagram
	@echo "$(GREEN)Generating crew diagram...$(RESET)"
	@export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$$DYLD_LIBRARY_PATH" && \
	export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$$PKG_CONFIG_PATH" && \
	crewai flow plot

update-kb: ## Update knowledge base
	@./bin/update_kb.sh

##@ Cleanup

clean-pyc: ## Remove Python file artifacts
	@echo "$(GREEN)Removing Python artifacts...$(RESET)"
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete

clean-test: ## Remove test and coverage artifacts
	@echo "$(GREEN)Removing test artifacts...$(RESET)"
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -f coverage.xml
	rm -f bandit-report.json
	rm -f safety-report.json

clean-build: ## Remove build artifacts
	@echo "$(GREEN)Removing build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .uv/

clean-all: clean-pyc clean-test clean-build ## Remove all artifacts
	@echo "$(GREEN)✓ All artifacts removed$(RESET)"

clean: clean-all ## Alias for clean-all

##@ Dependency Management

show-deps: ## Show dependency tree
	@uv tree

show-outdated: ## Show outdated dependencies
	@uv pip list --outdated

sync: ## Sync dependencies with lock file
	@echo "$(GREEN)Syncing dependencies...$(RESET)"
	uv sync --locked

lock: ## Update lock file
	@echo "$(GREEN)Updating lock file...$(RESET)"
	uv lock
