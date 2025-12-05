#!/bin/bash

# --- 1. SET ENVIRONMENT & DIRECTORY ---
# This script should be run from the root of the project directory.

echo "--- LAUNCHING SEMANTIC SURFER ---"

# --- 0. CLEANUP PREVIOUS RUNS ---
echo "Cleaning up port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null

# --- 2. CHECK & SETUP ENVIRONMENT ---

# Check/Create Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check which python we are using
which python3

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please create one with ASSEMBLYAI_API_KEY."
    exit 1
fi

# Ensure .env variables are loaded (ignoring comments)
export $(grep -v '^#' .env | xargs)

# Check/Install Node.js Dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# --- 3. LAUNCH PYTHON BACKEND ---
echo "Starting Python Backend..."
# Use python3 and -u for unbuffered output (critical for real-time logs)
python3 -u main.py &
PYTHON_PID=$!

# Wait for server to start
echo "Waiting for server to initialize..."
sleep 3 # Give Python time to start WebSocket server

# --- 4. LAUNCH ELECTRON (Frontend) ---
echo "Starting Electron Frontend..."
# Use npx electron . to ensure we use the local electron dependency
npm start &
ELECTRON_PID=$!

# --- 5. CLEANUP ON EXIT ---
# Ensure both processes are killed when this script exits
trap "kill $PYTHON_PID $ELECTRON_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

echo "--- APPLICATION RUNNING. Press Ctrl+C to stop. ---"
echo "Python PID: $PYTHON_PID"
echo "Electron PID: $ELECTRON_PID"

# Keep script running to maintain the trap
wait $PYTHON_PID $ELECTRON_PID
