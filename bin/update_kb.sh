#!/usr/bin/env bash

# Get the directory of the script itself
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
# Assume the project root is one level up from the 'bin' directory
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Navigate to the project root
cd "$PROJECT_ROOT" || { echo "Failed to navigate to project root: $PROJECT_ROOT"; exit 1; }

echo "======================================================================"
echo " EpicNews Knowledge Base Updater"
echo "======================================================================"
echo "Project Root: $(pwd)"
echo "Running script: scripts/update_knowledge_base.py"
echo "Arguments: $@"
echo "----------------------------------------------------------------------"

uv run python scripts/update_knowledge_base.py "$@"

EXIT_CODE=$?

echo "----------------------------------------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Knowledge base update script finished successfully."
else
  echo "❌ Knowledge base update script failed or an error occurred (Exit Code: $EXIT_CODE)."
  echo "   Check the output above for details."
fi
echo "======================================================================"

exit $EXIT_CODE
