#!/bin/bash

# --- 1. SET ENVIRONMENT & DIRECTORY ---
# This script should be run from the root of the project directory.

echo "--- LAUNCHING SEMANTIC SURFER ---"

# --- 0. CLEANUP PREVIOUS RUNS ---
echo "Cleaning up port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null

# --- 2. ACTIVATE ENVIRONMENT ---
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Python virtual environment 'venv' not found."
    exit 1
fi

# Check which python we are using
which python3

# Ensure .env variables are loaded
export $(cat .env | xargs)

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
npx electron . &
ELECTRON_PID=$!

# --- 5. CLEANUP ON EXIT ---
# Ensure both processes are killed when this script exits
trap "kill $PYTHON_PID $ELECTRON_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

echo "--- APPLICATION RUNNING. Press Ctrl+C to stop. ---"
echo "Python PID: $PYTHON_PID"
echo "Electron PID: $ELECTRON_PID"

# Keep script running to maintain the trap
wait $PYTHON_PID $ELECTRON_PID