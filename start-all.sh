#!/bin/bash

# Province - Start All Services
# This script starts the backend API, LiveKit agent, and frontend in separate terminals

echo "🚀 Starting Province Services..."
echo ""

# Check if we're in the correct directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the province root directory"
    exit 1
fi

# Function to open a new terminal and run a command
open_terminal() {
    local title=$1
    local command=$2

    osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)\" && echo \"$title\" && $command"
    activate
end tell
EOF
}

# Start Backend API
echo "📦 Starting Backend API (FastAPI)..."
open_terminal "Province Backend API" "cd backend && source venv/bin/activate 2>/dev/null || true && python -m uvicorn province.main:app --reload --port 8000"

sleep 2

# Start LiveKit Agent
echo "🎙️  Starting LiveKit Agent..."
open_terminal "Province LiveKit Agent" "cd backend && source venv/bin/activate 2>/dev/null || true && python -m province.livekit.agent dev"

sleep 2

# Start Frontend
echo "🌐 Starting Frontend (Next.js)..."
open_terminal "Province Frontend" "cd frontend && npm run dev"

echo ""
echo "✅ All services started!"
echo ""
echo "Services running:"
echo "  • Backend API:    http://localhost:8000"
echo "  • Frontend:       http://localhost:3000"
echo "  • LiveKit Agent:  Health check at http://localhost:8080/health"
echo ""
echo "📝 Note: Check each terminal window for service status"
echo "🛑 To stop: Close the terminal windows or press Ctrl+C in each"
