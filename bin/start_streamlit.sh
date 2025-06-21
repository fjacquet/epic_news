#!/bin/bash
# Shell wrapper to start Streamlit app for epic_news
# Usage: ./bin/start_streamlit.sh [port]

set -e

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Set default port or use provided port
PORT=${1:-8501}

echo "🚀 Starting Streamlit app for epic_news..."
echo "📁 Project root: $PROJECT_ROOT"
echo "🌐 Port: $PORT"
echo "🔗 URL: http://localhost:$PORT"
echo ""

# Activate virtual environment and run Streamlit
if [ -d ".venv" ]; then
    echo "✅ Using virtual environment (.venv)"
    source .venv/bin/activate
fi

# Start Streamlit with the specified port
echo "⚡ Launching Streamlit..."
uv run streamlit run src/epic_news/bin/streamlit_app.py --server.port="$PORT" --server.headless=true

echo ""
echo "🏁 Streamlit app stopped."
