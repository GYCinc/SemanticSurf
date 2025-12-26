# Semantic Server - Controls Reference

## Interaction Model: Mouse & Touch

The UI is optimized for real-time pedagogical marking. Keyboard shortcuts are secondary to the high-fidelity click interface.

### 🎯 Marking & Knowledge Capture
*Immediate visual feedback and backend sync.*

- **Click a Word:** Marks a **Vocabulary Gap**. The word turns emerald green and bold.
- **Click an Empty Area (Line):** Marks the **Full Turn** (Expression/Grammar). The turn receives an emerald left border.
- **Automatic Sync:** Every click creates a corresponding **Analysis Card** in Sanity instantly.

### 📝 Live Observations
- **Executive Summary:** Use the persistent sidebar to type notes during class. These are bundled into the final LLM synthesis at session end.

---

## Navigation & System

- **Select Student:** Use the header dropdown (Synced from Hub/Local Cache).
- **End Session:** Click the **Terminate** button to run the HD Diarization and LLM via AssemblyAI pipeline.
- **Cmd + Q:** Exit Application.

---

## Launching the App

The authoritative way to start the environment:
```bash
./launch.sh
```
*Note: This script initializes the Python server, handles port cleanup, and launches the Electron viewer.*

---

## UI Troubleshooting

### macOS Traffic Lights
- The UI header includes a dedicated 110px padding zone on the left to prevent overlap with standard window controls.

### Blurred Text
- If text is blending into the background, the "Crimson Glass" edition has been tuned for high-contrast (85% card opacity). Ensure your monitor brightness is sufficient.

---

**The goal: Capture moments quickly, review deeply later.**