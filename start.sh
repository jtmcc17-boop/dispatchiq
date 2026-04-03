#!/bin/bash
# DispatchIQ — start both backend and frontend

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🚚 Starting DispatchIQ..."

# Start backend
echo "▶ Starting FastAPI backend on http://localhost:8000"
cd "$ROOT/backend"
source venv/bin/activate
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "▶ Starting React frontend on http://localhost:5173"
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ DispatchIQ running:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
