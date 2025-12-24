#!/bin/bash

# Semantic Server - Double-Click Launcher
# This file launches the Electron desktop app

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clear the terminal
clear

echo "🎤 Semantic Server - Desktop App"
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

# --- PYTHON VERSION ENFORCEMENT ---
# The following block strictly enforces the use of Python 3.13.11.
# This is a critical system requirement. No other version is permitted.
# Any deviation will cause an immediate and fatal system exit.

# Capture the exact version string of the 'python3' command.
# This executes 'python3 --version' and stores the output (e.g., "Python 3.13.11").
# We use the system python first to check, or assume venv usage.
# Since this script activates venv later, we should check the python that WILL be used.
# But 'source venv/bin/activate' changes the python context.

echo "🐍 Verifying Python Version..."

# We need to check the python version inside the venv if it exists, or the system python.
# If venv exists, we use it.
if [ -d "venv" ]; then
    PYTHON_CMD="venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

CURRENT_PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
REQUIRED_PYTHON_VERSION="Python 3.13.11"

# Compare the current version with the required version.
if [ "$CURRENT_PYTHON_VERSION" != "$REQUIRED_PYTHON_VERSION" ]; then
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "CRITICAL ERROR: INCORRECT PYTHON VERSION DETECTED"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo ""
    echo "The system requires exactly: $REQUIRED_PYTHON_VERSION"
    echo "You are currently running:   $CURRENT_PYTHON_VERSION"
    echo "Command used: $PYTHON_CMD"
    echo ""
    echo "This enforcement is hard-coded to prevent compatibility issues."
    echo "Please install Python 3.13.11 and ensure it is available."
    echo ""
    echo "Process aborted."
    echo ""
    echo "Press any key to close..."
    read -n 1
    exit 1
fi

echo "✅ Python Version Verified: $CURRENT_PYTHON_VERSION"


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
echo "✅ Semantic Server is running!"
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