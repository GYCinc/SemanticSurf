#!/bin/bash

# ESL Transcript Viewer - Electron Desktop App Launch
# Creates a small, resizable window perfect for OBS

echo "🚀 Starting ESL Transcript Viewer (Desktop App)..."
echo ""

# Check if Electron is installed
if [ ! -d "node_modules/electron" ]; then
    echo "📦 Installing Electron (first time only)..."
    npm install
    echo ""
fi

# Kill any existing process on port 8765
echo "Cleaning up port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null
sleep 1

# Start Python backend
echo "Starting Python backend..."
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 3

# Launch Electron app
echo "Launching desktop app..."
npm start &
ELECTRON_PID=$!

echo ""
echo "✅ Desktop app running!"
echo "   Backend PID: $BACKEND_PID"
echo "   Electron PID: $ELECTRON_PID"
echo "   WebSocket: ws://localhost:8765"
echo ""
echo "Window Controls:"
echo "   • Resize window for OBS capture"
echo "   • Cmd+T to toggle always-on-top"
echo "   • Cmd+Q to quit"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $ELECTRON_PID 2>/dev/null; exit 0" INT
wait