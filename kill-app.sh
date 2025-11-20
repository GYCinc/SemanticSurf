#!/bin/bash
echo "Stopping Semantic Surfer..."
pkill -f "python.*main.py"
pkill -f "electron.*AssemblyAI"
echo "All processes stopped!"
