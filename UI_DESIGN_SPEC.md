# UI Design Specification - Crimson Glass (Tactile Edition)

## Design Philosophy

**Sophisticated. Tactile. Cinematic. High-Fidelity.**

This is not a terminal. This is a high-end pedagogical sensor inspired by the precision of Jony Ive and the atmospheric depth of the Matrix.

## Visual Design

### Color Palette (Crimson Obsidian)
- **Background:** `radial-gradient(circle at 20% 20%, #5a0a0a 0%, #000000 100%)`
- **Glass Surface:** `rgba(25, 25, 25, 0.45)` with `blur(50px)`
- **Accent Emerald:** `#10b981` (Marked items)
- **Accent Crimson:** `#ef4444` (Tutor / Velocity)
- **Accent Sky:** `#38bdf8` (Student)

### Typography
- **UI & Controls:** 'Inter', sans-serif (Precision weights: 400-900)
- **Data & Timestamps:** 'JetBrains Mono' (Weight: 500)
- **Transcript Text:** Size: `1.2rem`, Line Height: `1.8`, Weight: `500` (Optimized for deep reading)

### Layering (Tactile Glass)
- **Z-Index 100:** Header & Modals (Maximum blur)
- **Z-Index 50:** Active Focus Sidebar
- **Z-Index 10:** Transcript Cards (Neomorphic lifting)
- **Z-Index 0:** Main Crimson Blur Gradient

## Interactive Experience

### Neomorphic Lifting
Cards are not flat. They use dual-shadow neomorphism:
- **Outer Dark:** `12px 12px 25px rgba(0, 0, 0, 0.6)`
- **Outer Light:** `-8px -8px 20px rgba(255, 255, 255, 0.03)`
- **Hover State:** Card lifts `12px` on the Y-axis, shadows deepen, and scale increases to `1.01`.

### Glassmorphism 2.0
- **Light Catching:** `1px` solid white top and left borders (`opacity: 0.3`) simulate a physical glass edge catching ambient light.
- **Saturation:** `saturate(180%)` ensures background colors remain vibrant through the blur.

### Pedagogical Feedback
- **Word Marking:** Click a word to toggle `.marked-word`. Immediate emerald underline (`3px`) and glow effect.
- **Turn Marking:** Click card background to toggle `.marked-turn`. Emerald left border (`8px`) and subtle green inner glow.

## Animation & Motion (Framer Motion)

### Physics-Based Entry
- **Turns:** `initial: { opacity: 0, y: 40, scale: 0.92 }` -> `animate: { opacity: 1, y: 0, scale: 1 }`
- **Words:** Spring-based hover scaling (`stiffness: 400, damping: 10`).

### Continuity
- **Layout Transitions:** `AnimatePresence` with `popLayout` mode ensures that removing a marked note causes others to slide smoothly into place rather than jumping.

## Technical Stack

### Frontend
- **Framework:** React 18 (Functional Components + Hooks)
- **Motion:** Framer Motion 10+ (Physics & Layout)
- **Styling:** Tailwind CSS (CDN Runtime)
- **Communication:** Native WebSocket (JSON Protocol)

## Performance Metrics

- **Responsiveness:** <16ms click-to-visual feedback loop.
- **Diarization Sync:** Automatic transition from "Rough Draft" live text to "HD Final" post-session text.
- **Resource Usage:** Optimized blur areas to maintain 60fps on modern macOS hardware.

## Deployment Environment

- **Container:** Electron (Native Chrome Runtime)
- **Window Chrome:** `hiddenInset` title bar with custom traffic light padding (`110px`).
- **Always on Top:** Toggleable via `Cmd+T` for teaching focus.

---

**Built for the "Flow State" of Teaching.**
