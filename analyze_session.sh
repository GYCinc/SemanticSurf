#!/bin/bash

# One-command session analysis and export
# Usage: ./analyze_session.sh sessions/session_..._Student-X.json

if [ -z "$1" ]; then
    echo "Usage: ./analyze_session.sh <session_file.json>"
    echo ""
    echo "Example:"
    echo "  ./analyze_session.sh sessions/session_2025-10-31_15-35-14_Student-X.json"
    exit 1
fi

SESSION_FILE="$1"

if [ ! -f "$SESSION_FILE" ]; then
    echo "Error: File not found: $SESSION_FILE"
    exit 1
fi

echo "📊 Analyzing session..."
echo ""

# Activate virtual environment
source venv/bin/activate

# --- STEP 1: Run Session Analysis ---
# This reads the session.json and creates the _analysis.json
echo "--- Step 1: Running Session Analysis ---"
python analyzers/session_analyzer.py "$SESSION_FILE"
ANALYSIS_EXIT_CODE=$?

if [ $ANALYSIS_EXIT_CODE -ne 0 ]; then
    echo "❌ Session analysis failed. Aborting."
    exit 1
fi

# This is the path to the _analysis.json file
ANALYSIS_FILE="${SESSION_FILE%.json}_analysis.json"
if [ ! -f "$ANALYSIS_FILE" ]; then
    echo "❌ Analysis script ran but output file was not found: $ANALYSIS_FILE"
    exit 1
fi
echo "✅ Analysis complete."


# --- STEP 2: Generate Internal HTML Report (For Teacher) ---
echo "--- Step 2: Generating Teacher HTML Report ---"
python analyzers/generate_report.py "$ANALYSIS_FILE"
echo "✅ Teacher report complete."


# --- STEP 3: Generate External Student Report (For Student) ---
echo "--- Step 3: Generating Student Markdown Export ---"
# This runs your existing student_export.py script.
# It uses the original session.json, which is fine because
# that script is built to ALSO load the _analysis.json file.
python analyzers/student_export.py "$SESSION_FILE" markdown
echo "✅ Student export complete."


# --- FINAL SUMMARY ---
# Get all the new filenames
REPORT_FILE="${ANALYSIS_FILE%.json}_report.html"
STUDENT_FILE="sessions/student_export_${SESSION_FILE%.json}_.md" # Approximate name
STUDENT_FILE=$(ls sessions/student_export_*.md | tail -n 1) # Get the exact name


echo ""
echo "🎉 Analysis pipeline complete!"
echo ""
echo "📄 Files generated:"
echo "   Analysis JSON: $ANALYSIS_FILE"
echo "   Teacher Report: $REPORT_FILE"
echo "   Student Export: $STUDENT_FILE"
echo ""
echo "🌐 Opening TEACHER report in browser..."
open "$REPORT_FILE"
