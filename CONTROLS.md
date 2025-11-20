# ESL Transcript Viewer - Controls Reference

## Quick Controls Guide

### 🎯 How to Mark Sentences

**The workflow is simple:**

1. **Watch the transcript scroll** (recording continues automatically)
2. **See something interesting?** Press a number key to mark it
3. **That's it!** The line gets marked and saved

### ⌨️ Keyboard Controls (Default)

#### Marking (Works Anytime - Even While Scrolling!)
```
7 or Numpad 7  →  Mark FRONT of current/last line
8 or Numpad 8  →  Mark ENTIRE line (whole sentence)
9 or Numpad 9  →  Mark BACK of current/last line
5 or Numpad 5  →  Clear mark from selected line
```

#### Navigation
```
Arrow Up    →  Select previous line
Arrow Down  →  Select next line
Spacebar    →  Pause DISPLAY (recording continues!)
```

#### Other
```
E  →  Export session to JSON
?  →  Show help
```

### 📱 Touch Controls

```
Tap line       →  Select it
Swipe Left     →  Mark front
Swipe Right    →  Mark back
Double Tap     →  Mark entire line
```

### 🎬 For OBS Capture

**Desktop App (Recommended):**
```bash
./start-electron.sh
```

**Window Features:**
- Small, resizable window (600x400 default)
- Resize to fit your OBS scene
- Cmd+T to toggle always-on-top
- Perfect for screen capture

**Browser (Alternative):**
```bash
./start.sh
```
- Resize browser window as needed
- Works but less flexible

## Workflow Examples

### Example 1: Mark Pronunciation Error
```
Student says: "I go to store yesterday"
You hear error on "store" (missing article)
→ Press 8 (mark whole sentence)
→ Continue listening
→ Review later with voice notes
```

### Example 2: Mark Good Usage
```
Student says: "Although it was raining, I went outside"
Perfect complex sentence!
→ Press 8 (mark whole sentence)
→ Praise them later
```

### Example 3: Mark Specific Part
```
Student says: "I have been going to school every day"
Perfect tense usage at start, but ends weakly
→ Press 7 (mark front - the good part)
OR
→ Press 9 (mark back - the weak part)
```

### Example 4: Quick Marking While Teaching
```
Class is ongoing, student speaking...
→ Just tap 7, 8, or 9 when you hear something
→ Recording continues
→ Display keeps scrolling
→ Mark is saved with timestamp
→ Review all marks after class
```

## Understanding the Marks

### Visual Indicators
- `▸ text [F]` = Front marked
- `▸ text [A]` = All marked (entire sentence)
- `▸ text [B]` = Back marked

### In Saved JSON
```json
{
  "turn_order": 5,
  "transcript": "i go to store yesterday",
  "marked": true,
  "mark_type": "all",
  "mark_timestamp": "2024-10-30T14:32:15.234Z",
  "words": [...]
}
```

## Your Workflow (As Described)

1. **During Class:**
   - Student speaks
   - Transcript appears
   - You hear error/good usage
   - Press 7/8/9 to mark location
   - Keep teaching (no interruption!)

2. **After Class:**
   - Press E to export JSON
   - Open JSON file
   - See all marked sentences
   - Record voice notes over them
   - Fast review process!

## Customizing Keys

Don't like the defaults? Edit [`keyboard_config.json`](keyboard_config.json:1):

```json
{
  "bindings": {
    "pause_resume": "p",     // Change Spacebar to P
    "mark_front": "q",       // Change 7 to Q
    "mark_all": "w",         // Change 8 to W
    "mark_back": "e"         // Change 9 to E
  }
}
```

Reload the app to apply changes.

## Tips

- **Don't overthink it** - Just mark when you hear something
- **Mark type doesn't matter much** - You'll know what it was when you review
- **Fast marking** - Numpad is designed for speed
- **Silent operation** - No sounds, no popups
- **Keep teaching** - Marking doesn't interrupt the flow

---

**The goal: Capture moments quickly, review deeply later.**