#!/usr/bin/env bash

# Get the directory of the script itself
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
# Assume the project root is one level up from the 'bin' directory
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Navigate to the project root
cd "$PROJECT_ROOT" || { echo "Failed to navigate to project root: $PROJECT_ROOT"; exit 1; }

echo "======================================================================"
echo " EpicNews Test Suite & Coverage Report Runner"
echo "======================================================================"
echo "Project Root: $(pwd)"
echo "Running tests from: ./tests/"
echo "Calculating coverage for: ./src/epic_news/tools/"
echo "HTML coverage report will be generated in: ./htmlcov/"
echo "----------------------------------------------------------------------"
SENTRY_DSN="" DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH uv run pytest tests/ --cov=src --cov-report=html

EXIT_CODE=$?

echo "----------------------------------------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ All tests passed and coverage report generated successfully!"
  echo "   View the HTML report at: htmlcov/index.html"
else
  echo "❌ Some tests failed or an error occurred (Exit Code: $EXIT_CODE)."
  echo "   Check the output above for details. If coverage was generated,"
  echo "   it might be in: htmlcov/index.html"
fi
echo "======================================================================"

exit $EXIT_CODE
