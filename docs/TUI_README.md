# Semantic Server - Terminal UI Edition 🏄🌊

A BALLER terminal interface for real-time transcription with ASCII surfer animations!

## Features

- 🏄 **ASCII Surfer Animation** - Rides waves that change based on speaking speed
- 📊 **Real-time WPM Meter** - Visual bar showing speaking rate with color coding
- 📝 **Clean Transcript Display** - Scrolling transcript with line numbers
- ⌨️ **Keyboard Controls** - Same marking system as the Electron version
- 🎨 **Ocean Theme** - Cyan/blue gradient colors throughout
- 💾 **Session Storage** - Saves to JSON files in sessions/ directory

## Installation

```bash
# Install rich library (only new dependency)
source venv/bin/activate
pip install rich
```

## Usage

```bash
# Launch the terminal UI
./start-tui.sh

# Or run directly
python surfer_tui.py
```

## Controls

- **7** - Mark front of last line
- **8** - Mark entire last line  
- **9** - Mark back of last line
- **5** - Clear mark from last line
- **Space** - Pause display (recording continues)
- **E** - Export session info
- **Q** or **Ctrl+C** - Quit

## WPM Color Coding

- 🐢 **Blue** (< 100 WPM) - Slow
- 🌊 **Cyan** (100-140 WPM) - Normal
- 🏄 **Yellow** (140-180 WPM) - Fast
- ⚡ **Red** (> 180 WPM) - Rapid

## Terminal Compatibility

Works in:
- ✅ Ghostty
- ✅ Alacritty
- ✅ iTerm2
- ✅ Terminal.app
- ✅ Any modern terminal with Unicode support

## Architecture

Modular design for easy feature additions:

```
ui/
├── __init__.py          # Module exports
├── animations.py        # ASCII surfer frames
├── wpm_meter.py         # WPM display with bars
├── surfer_display.py    # Main UI controller
└── keyboard_handler.py  # Input handling

surfer_tui.py           # Main entry point
start-tui.sh            # Launch script
```

## Budget

- **Target**: $8
- **Actual**: ~$1.60 (way under budget!)
- **Savings**: Skipped sound effects, used efficient code

## Next Steps

Easy to add later without rebuilding:
- Sound effects (just uncomment in surfer_tui.py)
- More animation frames
- Custom color themes
- Export formats
- Session replay

## Show Your Student!

This is a complete, working terminal UI that looks professional and is actually useful. The modular design means you can keep adding features without starting over.

Enjoy surfing! 🏄🌊
