#!/bin/bash
# Start both backend and frontend dev servers
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Ensure data directories exist
mkdir -p "$PROJECT_DIR/data/photos" "$PROJECT_DIR/data/thumbnails"

# Start backend
echo "Starting backend..."
cd "$PROJECT_DIR/backend"
python -m uvicorn rewind.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend..."
cd "$PROJECT_DIR/frontend"
npm run dev -- --port 5173 &
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both servers"

wait
