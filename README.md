# Semantic Server

## Precision Transcription & Analysis Tool for GitEnglishHub

Semantic Server is a high-performance desktop application built for ESL teachers. It acts as a "Smart Capture" layer that records sessions, performs deep linguistic analysis using a tiered Python/LLM pipeline, and syncs curated knowledge to the GitEnglishHub platform.

---

## 🚀 Core Capabilities

1.  **"Crimson Glass" UI:** A professionally polished, high-contrast interface featuring tactile glassmorphism and neomorphic depth.
2.  **Tiered Analysis Pipeline:** Combines blazing-fast local Python metrics (POS, Verbs, N-grams) with deep AI reflection (Gemini 1.5 Pro).
3.  **Unified Sync:** Automatically packages transcripts, tutor notes, and analysis into a single payload for the GitEnglishHub API.
4.  **Marking System:** Click a word to tag a **Vocabulary Gap** or a line to tag a **Grammar Error**. Artifacts "Exist" in Sanity instantly.
5.  **Diarization HD:** Uses a dual-pass approach (Real-time rough draft -> Batch HD final cut) for 99% speaker accuracy.

---

## 🏁 Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Enter your ASSEMBLYAI_API_KEY and MCP_SECRET

# 2. Launch the app
./launch.sh
```

---

## 🔄 The Workflow: Capture to Curation

### 1. Live Session
- Teach as usual. The transcript scrolls automatically with live WPM tracking.
- **Marking:** Click words or lines to identify focus points.
- **Notes:** Use the sidebar to jot down executive observations.

### 2. Automatic Post-Processing
- Clicking **END SESSION** triggers the automated pipeline:
  - **HD Diarization:** Corrects speaker labels using the high-quality audio file.
  - **Linguistic Suite:** Runs local Python analyzers to extract hard data.
  - **AI Synthesis:** Gemini 1.5 Pro generates a structured session report.

### 3. Manual Curation
- Data is sent to the **GitEnglishHub Inbox**.
- Teachers review "Pending Words" on the Hub dashboard to manually commit them to the student's **Corpus**.

---

## ⚖️ The "Happens" vs "Exists" Rule

- **Analysis Cards** are "What Exists" (Lesson Artifacts) -> Stored in **Sanity**.

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `launch.sh` | The definitive app launcher. |
| `main.py` | Backend orchestrator and analysis controller. |
| `viewer2.html` | High-fidelity Electron UI. |
| `analyzers/` | Tiered local NLP suite. |

---

*This is a data capture tool. For student dashboards, visit [www.gitenglish.com](https://www.gitenglish.com).*
