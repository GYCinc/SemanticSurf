# Semantic Surfer - Installation Guide

## Quick Start (Development Mode)

### 1. Run from Terminal
```bash
./start-electron.sh
```
This starts both the Python backend and Electron app together.

## Build Desktop App (Install to Applications)

### 1. Install Build Dependencies
```bash
npm install
```

### 2. Build the App
```bash
chmod +x build-app.sh
./build-app.sh
```

This creates:
- `dist/Semantic Surfer-1.0.0.dmg` - Installer
- `dist/mac/Semantic Surfer.app` - The actual app

### 3. Install to Applications
```bash
# Option A: Use the DMG installer
open dist/Semantic\ Surfer-1.0.0.dmg
# Then drag to Applications folder

# Option B: Copy directly
cp -r "dist/mac/Semantic Surfer.app" /Applications/
```

### 4. Launch the App
```bash
# From Spotlight
# Press Cmd+Space, type "Semantic Surfer"

# Or from Terminal
open -a "Semantic Surfer"

# Or from Applications folder
# Double-click in Finder
```

## Important Notes

### Backend Requirement
The desktop app is just the **viewer**. You still need to run the Python backend separately:

```bash
# In a terminal, from the project directory:
./start.sh
```

Or keep it running in the background:
```bash
./start.sh &
```

### Why Separate Backend?
- Python needs access to your microphone
- Virtual environment (venv) can't be bundled easily
- Keeps the app lightweight
- Easier to update backend independently

## Usage

### Starting Everything
```bash
# Terminal 1: Start backend
./start.sh

# Terminal 2: Launch app (if installed)
open -a "Semantic Surfer"

# OR: Use the combined launcher
./start-electron.sh
```

### Keyboard Shortcuts
- **Cmd+T** - Toggle always-on-top (for OBS)
- **Cmd+Q** - Quit app
- **Cmd+R** - Reload viewer
- **Cmd+Shift+I** - Open DevTools (debugging)

### Window Controls
- Resize window for OBS capture
- Always-on-top mode for overlays
- Minimal, clean interface

## Troubleshooting

### "App can't be opened" (macOS Security)
```bash
# Remove quarantine flag
xattr -cr "/Applications/Semantic Surfer.app"

# Or: System Preferences > Security & Privacy > Open Anyway
```

### Backend Not Connecting
1. Make sure Python backend is running: `./start.sh`
2. Check WebSocket is on port 8765: `lsof -i :8765`
3. Reload the app: Cmd+R

### Build Fails
```bash
# Clean and rebuild
rm -rf node_modules dist
npm install
./build-app.sh
```

## File Structure

```
Semantic Surfer/
├── electron-main.js       # Desktop app entry point
├── viewer.html            # UI
├── main.py               # Python backend
├── package.json          # App configuration
├── build-app.sh          # Build script
├── start-electron.sh     # Combined launcher
└── dist/                 # Built apps (after build)
    ├── Semantic Surfer-1.0.0.dmg
    └── mac/
        └── Semantic Surfer.app
```

## Advanced: Auto-Start Backend

To make the app fully standalone, you could:

1. **Create a wrapper script** that starts both
2. **Use launchd** to keep backend running
3. **Bundle Python** with PyInstaller (complex)

For now, the two-process approach is simpler and more flexible.

## Uninstall

```bash
# Remove app
rm -rf "/Applications/Semantic Surfer.app"

# Remove build files
rm -rf dist node_modules

# Keep your session data
# (sessions/ directory is preserved)
```

---

**Need help?** Check the main README.md or open an issue.