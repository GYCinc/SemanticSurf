#!/bin/bash

# Semantic Surfer - Build Desktop App
# Creates an installable .dmg for macOS

echo "🏗️  Building Semantic Surfer Desktop App..."
echo ""

# Check if electron-builder is installed
if [ ! -d "node_modules/electron-builder" ]; then
    echo "📦 Installing build dependencies..."
    npm install
    echo ""
fi

# Build the app
echo "Building macOS app..."
npm run build:mac

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Installer created in: ./dist/"
echo ""
echo "To install:"
echo "  1. Open dist/Semantic Surfer-1.0.0.dmg"
echo "  2. Drag Semantic Surfer to Applications"
echo "  3. Launch from Applications or Spotlight"
echo ""
echo "Note: The Python backend (main.py) must be running separately."
echo "      Use ./start.sh to start the backend."