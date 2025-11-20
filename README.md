# Semantic Surfer - ESL Transcription & Analysis System

Complete real-time transcription and comprehensive ESL analysis platform for language learning.

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system architecture, hybrid stack documentation, and workflows.

## Quick Start

### Option 1: Easy Launch (Recommended)
```bash
./start.sh
```

### Option 2: Manual Launch
```bash
# Terminal 1: Start backend
source venv/bin/activate
# For WebSocket server (for browser viewer)
python main.py
# For Terminal UI
python main.py --tui

# Terminal 2 or Browser: Open viewer (if not using TUI)
open viewer.html
```

## 🎯 System Overview

This is a **complete ESL transcription and analysis system** with two main phases:

1. **🔴 Live Phase**: Real-time transcription and marking
2. **📊 Analysis Phase**: Comprehensive post-session analysis

---

## 🔴 Live Processing Scripts

### `main.py` - Core Transcription Engine
- Real-time streaming to AssemblyAI
- Word-level accuracy with millisecond timestamps
- Automatic speaking rate calculation
- Pause detection and fluency analysis
- WebSocket server for browser communication
- Session management with automatic JSON saving
- Can be run in two modes:
    - **WebSocket server mode (default):** for use with the `viewer.html` browser interface.
    - **Terminal UI mode (`--tui`):** for a standalone terminal-based interface.

### `check_audio.py` - Audio Device Detection
```bash
python check_audio.py
```
- Lists all available audio input devices
- Recommends optimal device for multi-channel audio
- Required before first run to select correct device in `config.json`

---

## 📊 Post-Processing Analysis Scripts

### `analyzers/session_analyzer.py` - Comprehensive Analysis
```bash
python analyzers/session_analyzer.py sessions/session_2025-10-31_15-35-14.json
```
Generates detailed ESL insights:
- **Speaking Rate Analysis**: WPM tracking vs native benchmarks
- **Fluency Assessment**: Pause patterns and struggling moments
- **Vocabulary Complexity**: CEFR level estimation
- **Filler Word Detection**: Fluency impact assessment
- **Repetition Analysis**: Overused word detection
- **Passion Moments**: High engagement topic identification
- **Grammar Patterns**: Basic error pattern recognition

### `analyzers/generate_report.py` - Visual Reports
```bash
python analyzers/generate_report.py sessions/session_2025-10-31_15-35-14_analysis.json
```
Creates beautiful HTML reports with:
- Interactive metric dashboards
- Visual charts and progress indicators
- Color-coded insights
- Professional styling for sharing

### `analyzers/student_export.py` - Multi-Format Exports
```bash
# Export specific format
python analyzers/student_export.py sessions/session_2025-10-31_15-35-14.json markdown

# Export all formats at once
python analyzers/student_export.py sessions/session_2025-10-31_15-35-14.json all
```
Supports 8 formats:
- **Markdown**: Universal format (Notion, Obsidian)
- **Notion**: Database-compatible with properties
- **OneNote**: HTML with proper styling
- **Google Docs**: Import-ready HTML
- **Obsidian**: Markdown with YAML frontmatter
- **Evernote**: ENEX XML format
- **Email**: Inline-styled HTML
- **Plain Text**: Universal compatibility

### `analyzers/export_marked_with_context.py` - LLM Integration
```bash
python analyzers/export_marked_with_context.py sessions/session_2025-10-31_15-35-14.json
```
Extracts marked turns with context for AI analysis:
- 3 turns of context before/after each marked moment
- Optimized for language model input
- Handles overlapping contexts intelligently

## 🔧 Utility Scripts

### `view_marked.py` - Quick Mark Review
```bash
python view_marked.py sessions/session_2025-10-31_15-35-14.json
```
- Terminal-based marked moments viewer
- Shows mark type, turn number, and transcript
- Quick review before detailed analysis

### `archive_sessions.sh` - Automatic Cleanup
```bash
./archive_sessions.sh
```
- Archives sessions older than 30 days
- Automatic space management
- Preserves recent sessions for analysis

## 🎮 Controls & Features

### Live Session Controls
- **Spacebar** - Pause/Resume stream
- **Numpad 7** - Mark front of sentence
- **Numpad 8** - Mark entire sentence  
- **Numpad 9** - Mark back of sentence
- **Numpad 5** - Clear mark
- **Arrow Up/Down** - Navigate lines (when paused)
- **E** - Export session to JSON
- **?** - Show help

### Touch Support
- **Tap** - Select line
- **Swipe Left** - Mark front
- **Swipe Right** - Mark back
- **Double Tap** - Mark all

## Customizing Keyboard

Edit `keyboard_config.json` to change any key binding:

```json
{
  "bindings": {
    "pause_resume": "p",        // Change from Spacebar to 'p'
    "mark_front": "q",           // Change from Numpad7 to 'q'
    "mark_all": "w",             // Change from Numpad8 to 'w'
    "mark_back": "e"             // Change from Numpad9 to 'e'
  }
}
```

Reload the page to apply changes.

## Data Storage

### Session Files
All sessions saved to `sessions/` directory:
```
sessions/
├── session_2024-10-30_14-30-15.json
├── session_2024-10-30_15-45-22.json
└── archive/                          # Auto-archived old sessions
```

### Session Format
```json
{
  "session_id": "abc123",
  "start_time": "2024-10-30T14:30:15.123Z",
  "end_time": "2024-10-30T14:35:42.789Z",
  "total_turns": 45,
  "total_words": 234,
  "turns": [
    {
      "turn_order": 1,
      "transcript": "i go to store",
      "speaker": "Aaron",
      "end_of_turn": true,
      "end_of_turn_confidence": 0.87,
      "marked": true,
      "mark_type": "front",
      "words": [
        {
          "text": "i",
          "start_ms": 1234,
          "end_ms": 1456,
          "duration_ms": 222,
          "confidence": 0.95,
          "word_is_final": true
        }
      ],
      "analysis": {
        "word_count": 4,
        "speaking_rate_wpm": 145.2,
        "pause_count": 2,
        "total_pause_time_ms": 850
      }
    }
  ]
}
```

## Performance

- **Load time**: <100ms
- **Frame rate**: 60fps constant
- **Memory**: <50MB
- **File size**: ~90KB per hour of speech

## Privacy

- ✅ All data saved locally
- ✅ No cloud storage
- ✅ AssemblyAI processes audio (necessary for transcription)
- ⚠️ Check AssemblyAI privacy policy for student consent

## Troubleshooting

### Port already in use
```bash
lsof -ti:8765 | xargs kill -9
```

### Backend not starting
```bash
source venv/bin/activate
pip install assemblyai python-dotenv websockets
```

### Browser not connecting
1. Check backend is running (should see "WebSocket server started")
2. Check console for errors (F12 in browser)
3. Verify port 8765 is open

### Python Environment Issues
**Two virtual environments exist:**
- `./venv/` ✅ **Use this one** (Python 3.13.9 - Compatible)
- `./semantic_surfer_venv/` ❌ **Ignore this** (Python 3.14.0 - Incompatible)

All scripts correctly reference `./venv/`. If issues persist:
```bash
source venv/bin/activate
python --version  # Should show 3.13.x
```

## 📁 Project Structure

```
/Users/thelaw/AssemblyAI/
├── main.py                          # Live transcription engine
├── check_audio.py                   # Audio device detection
├── view_marked.py                   # Marked turns viewer
├── archive_sessions.sh              # Session cleanup
├── start.sh                         # Easy launcher
├── fix_audio.sh                     # Audio troubleshooting
├── electron-main.js                 # Desktop app wrapper
├── config.json                      # Configuration
├── keyboard_config.json             # Key bindings
├── .env                            # API keys (protected)
├── .gitignore                      # Git ignore rules
├── venv/                           # ✅ Working Python environment
├── semantic_surfer_venv/            # ❌ Broken Python environment
├── analyzers/                       # Post-processing scripts
│   ├── session_analyzer.py          # Comprehensive analysis
│   ├── generate_report.py           # HTML report generator
│   ├── student_export.py            # Multi-format exporter
│   └── export_marked_with_context.py # LLM-ready extraction
├── sessions/                        # Session storage
│   ├── session_2025-10-31_*.json    # Individual sessions
│   └── archive/                     # Archived sessions
└── quests/                          # Electron app components
```

## 📊 Complete Workflow Example

```bash
# 1. Setup (first time only)
python check_audio.py  # Find your device
# Edit config.json with correct device_index

# 2. Live Session
./start.sh  # Starts transcription and viewer
# Mark moments during the lesson

# 3. Post-Session Analysis
python analyzers/session_analyzer.py sessions/session_*.json
python analyzers/generate_report.py sessions/session_*_analysis.json
python analyzers/student_export.py sessions/session_*.json all

# 4. Review Results
python view_marked.py sessions/session_*.json
open sessions/session_*_report.html
open sessions/student_exports/
```

## 🎯 Key Features

### Live Processing
- **Real-time transcription** with AssemblyAI streaming
- **Word-level timestamps** for precise analysis
- **Speaking rate calculation** on the fly
- **Pause detection** for fluency assessment
- **Browser-based marking** interface

### Post-Processing Analysis
- **8 different export formats** for student sharing
- **Visual HTML reports** with metrics dashboard
- **Comprehensive ESL insights** (fluency, complexity, passion)
- **LLM-ready data** for AI-assisted analysis
- **Automatic session archiving**

### Data & Privacy
- **Local JSON storage** - All data stays on your machine
- **Privacy-focused** - No cloud storage of transcripts
- **Immutable transcripts** - Errors preserved for learning
- **Word-level precision** - Millisecond accuracy
- **Complete metadata** - Full analysis capability

## ⚙️ Technical Notes

- **AssemblyAI SDK** for real-time transcription
- **PyAudio** for multi-channel audio handling
- **WebSockets** for browser communication
- **Pure HTML/CSS/JS** for zero-dependency viewer
- **Python 3.13.9** required (venv environment)
- **~90KB per hour** of speech in storage

---

**Complete ESL transcription and analysis system. Live capture. Deep insights. Student-ready exports.**
Reload the page to apply changes.

## Data Storage

### Session Files
All sessions saved to `sessions/` directory:
```
sessions/
├── session_2024-10-30_14-30-15.json
├── session_2024-10-30_15-45-22.json
└── archive/                          # Auto-archived old sessions
```

### Session Format
```json
{
  "session_id": "abc123",
  "start_time": "2024-10-30T14:30:15.123Z",
  "end_time": "2024-10-30T14:35:42.789Z",
  "total_turns": 45,
  "total_words": 234,
  "turns": [
    {
      "turn_order": 1,
      "transcript": "i go to store",
      "speaker": "Aaron",
      "end_of_turn": true,
      "end_of_turn_confidence": 0.87,
      "marked": true,
      "mark_type": "front",
      "words": [
        {
          "text": "i",
          "start_ms": 1234,
          "end_ms": 1456,
          "duration_ms": 222,
          "confidence": 0.95,
          "word_is_final": true
        }
      ],
      "analysis": {
        "word_count": 4,
        "speaking_rate_wpm": 145.2,
        "pause_count": 2,
        "total_pause_time_ms": 850
      }
    }
  ]
}
```

## Performance

- **Load time**: <100ms
- **Frame rate**: 60fps constant
- **Memory**: <50MB
- **File size**: ~90KB per hour of speech

## Privacy

- ✅ All data saved locally
- ✅ No cloud storage
- ✅ AssemblyAI processes audio (necessary for transcription)
- ⚠️ Check AssemblyAI privacy policy for student consent

## Troubleshooting

### Port already in use
```bash
lsof -ti:8765 | xargs kill -9
```

### Backend not starting
```bash
source venv/bin/activate
pip install assemblyai python-dotenv websockets
```

### Browser not connecting
1. Check backend is running (should see "WebSocket server started")
2. Check console for errors (F12 in browser)
3. Verify port 8765 is open

### Python Environment Issues
**Two virtual environments exist:**
- `./venv/` ✅ **Use this one** (Python 3.13.9 - Compatible)
- `./semantic_surfer_venv/` ❌ **Ignore this** (Python 3.14.0 - Incompatible)

All scripts correctly reference `./venv/`. If issues persist:
```bash
source venv/bin/activate
python --version  # Should show 3.13.x
```

## 📁 Project Structure

```
/Users/thelaw/AssemblyAI/
├── main.py                          # Live transcription engine
├── check_audio.py                   # Audio device detection
├── view_marked.py                   # Marked turns viewer
├── archive_sessions.sh              # Session cleanup
├── start.sh                         # Easy launcher
├── fix_audio.sh                     # Audio troubleshooting
├── electron-main.js                 # Desktop app wrapper
├── config.json                      # Configuration
├── keyboard_config.json             # Key bindings
├── .env                            # API keys (protected)
├── .gitignore                      # Git ignore rules
├── venv/                           # ✅ Working Python environment
├── semantic_surfer_venv/            # ❌ Broken Python environment
├── analyzers/                       # Post-processing scripts
│   ├── session_analyzer.py          # Comprehensive analysis
│   ├── generate_report.py           # HTML report generator
│   ├── student_export.py            # Multi-format exporter
│   └── export_marked_with_context.py # LLM-ready extraction
├── sessions/                        # Session storage
│   ├── session_2025-10-31_*.json    # Individual sessions
│   └── archive/                     # Archived sessions
└── quests/                          # Electron app components
```

## 📊 Complete Workflow Example

```bash
# 1. Setup (first time only)
python check_audio.py  # Find your device
# Edit config.json with correct device_index

# 2. Live Session
./start.sh  # Starts transcription and viewer
# Mark moments during the lesson

# 3. Post-Session Analysis
python analyzers/session_analyzer.py sessions/session_*.json
python analyzers/generate_report.py sessions/session_*_analysis.json
python analyzers/student_export.py sessions/session_*.json all

# 4. Review Results
python view_marked.py sessions/session_*.json
open sessions/session_*_report.html
open sessions/student_exports/
```

## 🎯 Key Features

### Live Processing
- **Real-time transcription** with AssemblyAI streaming
- **Word-level timestamps** for precise analysis
- **Speaking rate calculation** on the fly
- **Pause detection** for fluency assessment
- **Browser-based marking** interface

### Post-Processing Analysis
- **8 different export formats** for student sharing
- **Visual HTML reports** with metrics dashboard
- **Comprehensive ESL insights** (fluency, complexity, passion)
- **LLM-ready data** for AI-assisted analysis
- **Automatic session archiving**

### Data & Privacy
- **Local JSON storage** - All data stays on your machine
- **Privacy-focused** - No cloud storage of transcripts
- **Immutable transcripts** - Errors preserved for learning
- **Word-level precision** - Millisecond accuracy
- **Complete metadata** - Full analysis capability

## ⚙️ Technical Notes

- **AssemblyAI SDK** for real-time transcription
- **PyAudio** for multi-channel audio handling
- **WebSockets** for browser communication
- **Pure HTML/CSS/JS** for zero-dependency viewer
- **Python 3.13.9** required (venv environment)
- **~90KB per hour** of speech in storage

---

**Complete ESL transcription and analysis system. Live capture. Deep insights. Student-ready exports.**
