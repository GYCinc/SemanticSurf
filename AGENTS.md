# Semantic Surfer: System Workspace Rules 🏄‍♂️

Hello Agent. Welcome to the Semantic Surfer repository. This is a "Vibe Coding" environment. We prioritize flow, aesthetics, and reliability over boilerplate and complex build chains.

## 🌊 The Vibe Coding Philosophy

1.  **No Build Steps for Frontend:**
    *   We use runtime transpilation (Babel standalone) in `viewer2.html`.
    *   **Do not** introduce Webpack, Vite, or Parcel.
    *   The workflow is: Edit `viewer2.html` -> Refresh Electron window. Simple.

2.  **One Script to Rule Them All:**
    *   `./launch.sh` is the canonical entry point.
    *   It handles the `venv`, installs dependencies, and launches Electron.
    *   **Never** ask the user to run `npm start` or `python main.py` manually unless debugging a specific crash.

3.  **Keep it Clean:**
    *   Aggressively remove "technical debt" (unused scripts, `old_` files, temp files).
    *   Do not leave commented-out code blocks "just in case." Git history exists for that.

## 🎨 Visual Standards: "Crimson Glass"

The UI (`viewer2.html`) must adhere to the **Crimson Glass** aesthetic.

*   **Color Palette:**
    *   Primary Backgrounds: Deep Red Gradients (`from-[#450a0a] via-[#991b1b] to-[#450a0a]`).
    *   **Never** use pitch black (`#000000`). It looks dead.
    *   Headers/Dropdowns: Opaque with red borders.
*   **Animations:**
    *   Use **Spring Physics** (Bouncy).
    *   Framer Motion config: `{ type: "spring", stiffness: 300, damping: 20 }`.
    *   Interactive text must "staircase" or scale up on hover.
*   **Stability:**
    *   **Hardcode Critical Styles:** Put basic background/text colors in a `<style>` block in `<head>`. If Tailwind fails to load, the user shouldn't see a white screen.
    *   **Window Drag:** The window is frameless. The header needs `-webkit-app-region: drag`. Buttons inside it need `-webkit-app-region: no-drag`.

## 🧠 The Six Notable Noetics (Immutable)

The system enforces strictly **6 User-Facing Categories**. These are the "Six Notable Noetics".
All "nitty-gritty" linguistic phenomena (Petty Dantic) must map to one of these.

1.  **Grammar** (Morphology, Syntax, Structure)
2.  **Vocabulary** (Lexical Choice, Precision)
3.  **Phrasal Verbs** (Multi-word verbs)
4.  **Collocations** (Natural pairings)
5.  **Idioms & Phrases** (Fixed expressions, Cultural sayings)
6.  **Fluency & Flow** (Pragmatics, Discourse Markers, Tone, Speed)

**Do not introduce "Pronunciation" or "Structure" as top-level categories.** They are internal details mapped to the above (e.g., Pronunciation -> Fluency & Flow, Structure -> Grammar).

## 🏗️ Architecture & Safety

### Frontend (`viewer2.html`)
*   **Truncation Danger:** When editing this large file, ensure you do not truncate the end (closing `</script>` or `</body>` tags). This is a known issue. **Always verify the last 10 lines after writing.**
*   **Error Overlays:** Maintain `window.onerror` handlers to catch "White Screen of Death" issues (e.g., CDN failures).
*   **Race Conditions:** The UI receives `partial` and `final` transcripts. Handle them robustly to avoid flickering.

### Backend (`main.py` & `ingest_audio.py`)
*   **Pipeline:**
    *   `main.py` handles Real-time Websockets & Audio Streaming.
    *   `ingest_audio.process_and_upload` is the canonical handoff function triggered on "End Session".
*   **Speaker Labels:** Strictly use **"Speaker A"** and **"Speaker B"**.
    *   **Never** map these to names like "Student" or "Teacher" in the backend. Diarization relies on A/B consistency.

### Environment
*   **Environment Variables:** Stored in `.env`.
*   **Launch Script:** `launch.sh` must export these variables (filtering out comments) before starting the app.

## 🧪 Testing & Verification

*   **Frontend Verification:** Use `verify_dashboard.py` (Playwright) to check if UI elements (like the Notes widget) are rendering correctly.
*   **No "Teaching" Logic:** This repo is for *Analysis* only. Teaching agents belong in the external GitEnglishHub.
