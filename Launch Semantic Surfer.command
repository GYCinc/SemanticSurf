#!/bin/bash

# Semantic Surfer - Double-Click Launcher
# This file launches the Electron desktop app

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clear the terminal
clear

echo "🎤 Semantic Surfer - Desktop App"
echo "================================"
echo ""

# Check if Electron is installed
if [ ! -d "node_modules/electron" ]; then
    echo "📦 First time setup - Installing Electron..."
    echo "   This will take about 30 seconds..."
    echo ""
    npm install
    echo ""
fi

# Kill any existing process on port 8765
echo "🧹 Cleaning up..."
lsof -ti:8765 | xargs kill -9 2>/dev/null
sleep 1

# Start Python backend
echo "🐍 Starting backend..."
source venv/bin/activate && python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Initializing..."
sleep 3

# Launch Electron app
echo "🚀 Launching desktop app..."
echo ""
npm start &
ELECTRON_PID=$!

sleep 2
echo "✅ Semantic Surfer is running!"
echo ""
echo "💡 Tips:"
echo "   • Resize the window for OBS capture"
echo "   • Press Cmd+T to toggle always-on-top"
echo "   • Press Cmd+Q to quit"
echo ""
echo "⚠️  Keep this terminal window open"
echo "   Close it to stop the app"
echo ""

# Wait for Ctrl+C or window close
trap "echo ''; echo '👋 Shutting down...'; kill $BACKEND_PID $ELECTRON_PID 2>/dev/null; exit 0" INT TERM
wait