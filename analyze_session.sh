#!/bin/bash

# analyze_session.sh
# Automated Session Analysis Trigger
# Usage: ./analyze_session.sh [session_id] [student_name]

SESSION_ID=$1
STUDENT_NAME=$2

if [ -z "$SESSION_ID" ]; then
    echo "Usage: ./analyze_session.sh [session_id] [student_name]"
    exit 1
fi

echo "🚀 Triggering Analysis for Session: $SESSION_ID"

# Construct payload for Semantic Server
# We use curl to hit the local "Data Vacuum"
curl -X POST http://localhost:8080/analyze \
     -H "Content-Type: application/json" \
     -d '{ "student_name": "'