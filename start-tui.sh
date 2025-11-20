#!/bin/bash
# Launch Semantic Surfer Terminal UI

echo "🌊 Starting Semantic Surfer Terminal UI..."

# Use Python 3.13 explicitly for compatibility
PYTHON_BIN="/opt/homebrew/bin/python3.13"

# Check if Python 3.13 is available
if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Python 3.13 not found at $PYTHON_BIN"
    echo "Please install Python 3.13: brew install python@3.13"
    exit 1
fi

# Create or activate virtual environment with Python 3.13
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with Python 3.13..."
    $PYTHON_BIN -m venv venv
fi

source venv/bin/activate

# Check if rich is installed
if ! python -c "import rich" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install rich assemblyai python-dotenv pyaudio numpy
fi

# Make surfer_tui.py executable
chmod +x surfer_tui.py

# Run the TUI
python surfer_tui.py

