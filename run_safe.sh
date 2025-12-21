#!/bin/bash

# ENSURE PYTHON 3.13 IS USED (Permanently fixed per user request)
PYTHON_EXEC="/opt/homebrew/bin/python3.13"

if [ ! -f "$PYTHON_EXEC" ]; then
    echo "❌ Python 3.13 not found at $PYTHON_EXEC"
    exit 1
fi

echo "🚀 Running with verified Python 3.13..."
echo "Interpreter: $($PYTHON_EXEC --version)"

# Pass all arguments to the python script
$PYTHON_EXEC "$@"
