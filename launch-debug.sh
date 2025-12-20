#!/bin/bash
# Debug launcher - shows all errors

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🔍 Debug Mode - Semantic Server"
echo "================================"
echo ""

# Kill existing processes
lsof -ti:8765 | xargs kill -9 2>/dev/null
sleep 1

# Start backend with full error output
echo "🐍 Starting backend (errors will show below)..."
source venv/bin/activate

# Run Python with full error output
python main.py 2>&1 | tee backend-error.log &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Waiting 3 seconds..."
sleep 3

# Check if backend is still running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo ""
    echo "❌ BACKEND CRASHED!"
    echo "Error log saved to: backend-error.log"
    echo ""
    echo "Last 20 lines of error:"
    tail -20 backend-error.log
    exit 1
fi

echo ""
echo "✅ Backend running"
echo "🚀 Launching Electron..."
npm start

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
