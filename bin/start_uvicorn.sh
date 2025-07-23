#!/bin/bash
# Shell wrapper to start Uvicorn FastAPI server for epic_news
# Usage: ./bin/start_uvicorn.sh [port]

set -e

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Set default port or use provided port
PORT=${1:-8000}

echo "🚀 Starting Uvicorn FastAPI server for epic_news..."
echo "📁 Project root: $PROJECT_ROOT"
echo "🌐 Port: $PORT"
echo "🔗 API URL: http://localhost:$PORT"
echo "📚 API Docs: http://localhost:$PORT/docs"
echo ""

# Activate virtual environment and run Uvicorn
if [ -d ".venv" ]; then
    echo "✅ Using virtual environment (.venv)"
    source .venv/bin/activate
fi

# Start Uvicorn with the specified port
echo "⚡ Launching Uvicorn FastAPI server..."
uv run uvicorn src.epic_news.api:app --host 0.0.0.0 --port "$PORT"

echo ""
echo "🏁 Uvicorn server stopped."
