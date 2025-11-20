# UI Design Specification - Minimal, Fast, Non-Distracting

## Design Philosophy

**Simple. Fast. Terminal-like. Zero Bullshit.**

## Visual Design

### Color Palette (Dark Terminal Theme)
```css
Background:     #0a0a0a  (almost black)
Text:           #e0e0e0  (light gray)
Selected Line:  #1a1a1a  (subtle highlight)
Marked Line:    #0d3a1a  (dark green tint)
Status:         #3fb950  (green accent)
```

### Typography
```css
Font:           'SF Mono', 'Consolas', 'Monaco', monospace
Size:           16px (readable but compact)
Line Height:    1.6 (breathing room)
Letter Spacing: 0.5px (terminal-like)
```

### Layout
```
┌─────────────────────────────────────────────────────────┐
│ ● Connected                                    [PAUSED] │ ← Status bar (minimal)
├─────────────────────────────────────────────────────────┤
│                                                         │
│  i go to store                                          │ ← Line 1
│  yesterday i buy milk                                   │ ← Line 2 (selected)
│  but i forget bread                                     │ ← Line 3
│  so i go back                                           │ ← Line 4
│  ...                                                    │
│  (20 lines total)                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
                                                    ↑
                                            Numpad controls
                                            (invisible overlay)
```

## Performance Optimizations

### 1. **Virtual Scrolling**
- Only render visible lines (~20)
- Recycle DOM elements
- Smooth 60fps scrolling
- No lag even with 1000+ lines buffered

### 2. **Efficient Updates**
```javascript
// Only update changed text, not entire DOM
if (currentLine.text !== newText) {
    currentLine.textContent = newText;  // Direct DOM update
}
```

### 3. **Minimal Repaints**
- Use CSS transforms for selection highlight
- No layout thrashing
- GPU-accelerated animations
- Debounced scroll events

### 4. **Zero Dependencies**
- Pure HTML/CSS/JavaScript
- No React, no Vue, no frameworks
- Loads in <100ms
- Runs on potato computers

## Interactive Elements

### Selection Indicator (Subtle)
```css
.line.selected {
    background: #1a1a1a;           /* Barely visible */
    border-left: 2px solid #3fb950; /* Thin green line */
    padding-left: 8px;
}
```

### Marked Indicator (Even More Subtle)
```css
.line.marked {
    background: #0d3a1a;           /* Dark green tint */
    border-left: 2px solid #3fb950;
}

.line.marked::before {
    content: '▸ ';                 /* Small arrow */
    color: #3fb950;
    opacity: 0.5;
}
```

### Pause Indicator
```css
.paused-indicator {
    position: fixed;
    top: 10px;
    right: 10px;
    color: #f85149;
    font-size: 12px;
    animation: pulse 1s infinite;
}
```

## Keyboard Controls (Silent Operation)

### Visual Feedback (Minimal)
- **No sounds**
- **No popups**
- **No animations** (except subtle highlight)
- Just a brief flash on the marked line

### Numpad Layout
```
┌───┬───┬───┐
│ 7 │ 8 │ 9 │  7 = Mark FRONT
│   │   │   │  8 = Mark ALL
│   │   │   │  9 = Mark BACK
├───┼───┼───┤
│ 4 │ 5 │ 6 │  4/6 = Navigate left/right (future)
│   │   │   │  5 = Deselect/Clear
├───┼───┼───┤
│ 1 │ 2 │ 3 │  (Reserved for future)
│   │   │   │
└───┴───┴───┘
```

## Touch Controls

### Gestures
- **Tap** = Select line
- **Swipe Left** = Mark front
- **Swipe Right** = Mark back
- **Double Tap** = Mark all
- **Long Press** = Show quick stats (optional)

### Touch Targets
- Each line is 40px tall (easy to tap)
- Full-width touch area
- No tiny buttons

## What It Looks Like

### Normal State
```
┌─────────────────────────────────────────────────────────┐
│ ● Connected                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  i go to store                                          │
│  yesterday i buy milk                                   │
│  but i forget bread                                     │
│  so i go back                                           │
│  the store is close                                     │
│  i am sad                                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### With Selection
```
┌─────────────────────────────────────────────────────────┐
│ ● Connected                                    [PAUSED] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  i go to store                                          │
│ ▸yesterday i buy milk                                   │ ← Selected
│  but i forget bread                                     │
│  so i go back                                           │
│  the store is close                                     │
│  i am sad                                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### With Marks
```
┌─────────────────────────────────────────────────────────┐
│ ● Connected                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  i go to store                                          │
│ ▸yesterday i buy milk                                   │ ← Marked (front)
│  but i forget bread                                     │
│  so i go back                                           │
│ ▸the store is close                                     │ ← Marked (all)
│  i am sad                                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Technical Stack

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling, GPU acceleration
- **Vanilla JavaScript** - No frameworks, pure performance
- **WebSocket API** - Native browser support

### Why No Framework?
1. **Faster** - No bundle, no overhead
2. **Simpler** - Easy to understand and modify
3. **Lighter** - Loads instantly
4. **More Control** - Direct DOM manipulation

## Performance Metrics

### Target Performance
- **Initial Load**: <100ms
- **Frame Rate**: 60fps constant
- **Memory**: <50MB
- **CPU**: <5% idle, <15% active
- **Network**: WebSocket only (~1KB/s)

### Optimization Techniques
1. **RequestAnimationFrame** for smooth updates
2. **CSS containment** for layout optimization
3. **Will-change** hints for GPU acceleration
4. **Passive event listeners** for scroll
5. **Debounced keyboard** for rapid input

## Accessibility

### Keyboard-First Design
- All features accessible via keyboard
- No mouse required
- Silent operation (no audio feedback)
- Visual feedback only

### Screen Reader Support
- Semantic HTML
- ARIA labels where needed
- Live region for new transcripts

## OBS Integration

### Window Capture Friendly
- Clean, minimal UI
- No distracting elements
- High contrast for readability
- Scales well at different resolutions

### Recommended OBS Settings
- Window Capture (not Display Capture)
- Crop to content area
- Scale to fit
- No chroma key needed

## File Structure

```
/
├── index.html          (Main UI - ~200 lines)
├── styles.css          (Styling - ~150 lines)
├── app.js              (Logic - ~300 lines)
└── sessions/           (JSON storage)
    └── session_*.json
```

**Total Code**: ~650 lines of clean, readable code

## Summary

**What You Get:**
- ✅ Terminal-like aesthetic (dark, minimal)
- ✅ Blazing fast performance (60fps)
- ✅ Zero distractions (no fancy UI)
- ✅ Silent operation (keyboard-focused)
- ✅ Touch-screen ready
- ✅ OBS-friendly
- ✅ Professional but simple

**What You DON'T Get:**
- ❌ No fancy animations
- ❌ No colorful themes
- ❌ No unnecessary features
- ❌ No bloat

**It's a tool, not a toy. Fast, simple, effective.**