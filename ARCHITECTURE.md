# Semantic Surfer Architecture

## Overview

Semantic Surfer is a desktop application for real-time ESL tutoring. It captures audio, transcribes via AssemblyAI, performs AI analysis, and sends results to GitEnglishHub for storage.

**Semantic Surfer** = Desktop audio capture + real-time transcription
**GitEnglishHub** = Web dashboard + database storage + student-facing UI

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SEMANTIC SURFER (This Repo)                    │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Audio captured (mic or pre-recorded file)                        │
│ 2. AssemblyAI transcribes with speaker diarization                  │
│ 3. LeMUR analyzes linguistic phenomena                              │
│ 4. Results → Petty Dantic API (GitEnglishHub)                       │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GITENGLISHHUB                                   │
│             https://www.gitenglish.com                               │
├─────────────────────────────────────────────────────────────────────┤
│ POST /api/mcp  →  Petty Dantic Action Registry                      │
│ - ingest.createSession → student_sessions table                     │
│ - schema.addToCorpus → student_corpus table                         │
│ - sanity.createLessonAnalysis → Sanity CMS                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Audio Ingestion Methods

### Method 1: Live Streaming (`main.py`)

Real-time tutoring sessions with live transcription.

```bash
./launch.sh   # or: python main.py
```

- Streams mic audio to AssemblyAI
- Shows live transcript in Electron UI
- On session end → sends to GitEnglishHub

### Method 2: Pre-Recorded Script (`ingest_audio.py`)

Batch processing for recorded lessons.

```bash
python ingest_audio.py
```

- Dual-pass transcription (raw + diarized)
- LeMUR analysis extracts linguistic phenomena
- Creates session + populates corpus via API

### Method 3: Web UI (GitEnglishHub)

Upload directly from browser without running Semantic Surfer.

- URL: `https://www.gitenglish.com/admin/upload-audio`
- Uses AssemblyAI webhook for async processing
- No Python environment required

---

## Core Components

### Python Backend (`main.py`)

| Component                 | Purpose                    |
| ------------------------- | -------------------------- |
| `pyaudio`                 | Captures microphone audio  |
| `assemblyai.streaming.v3` | Real-time transcription    |
| `websockets`              | Broadcasts to Electron UI  |
| `send_to_gitenglish()`    | API calls to GitEnglishHub |

### Electron Frontend (`viewer2.html`, `electron-main.js`)

- Real-time transcript display
- Speaker diarization (A=Tutor, B=Student)
- Mark system for flagging teaching moments

### Pre-Recorded Ingestion (`ingest_audio.py`)

- Dual-pass: Raw (no punctuation) + Diarized (speaker labels)
- LeMUR analysis with linguistic prompt
- Batch corpus upload to GitEnglishHub

---

## Environment Variables

```bash
# Required
ASSEMBLYAI_API_KEY=your_key

# GitEnglishHub Connection (Required for data sync)
GITENGLISH_API_BASE=https://www.gitenglish.com
MCP_SECRET=shared_secret_must_match_gitenglishhub

# Optional (for local student lookup)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_key
```

> **CRITICAL:** `MCP_SECRET` must be identical in both Semantic Surfer and GitEnglishHub.

---

## Session Storage

### Local JSON (Backup)

Path: `sessions/{StudentName}_session_{Timestamp}.json`

Contains:

- All turns with speaker labels
- Word-level timestamps and confidence
- Analysis data (WPM, pauses)
- Tutor marks and notes

### Remote (GitEnglishHub)

- **Supabase `student_sessions`:** Session metadata + pending words
- **Supabase `student_corpus`:** Committed vocabulary entries
- **Sanity CMS:** Post-lesson analysis cards

---

## LeMUR Analysis

The `ingest_audio.py` script uses a detailed linguistic prompt to extract:

1. **Annotated Errors** - Quote, correction, category, explanation
2. **Student Profile** - CEFR estimate, dominant issue
3. **Prioritized Tasks** - HIGH/MEDIUM/LOW remedial activities

Categories: Syntax, Lexis, Pragmatics

---

## Corpus Commitment Flow

Words are NOT auto-committed. Human curation required:

1. Teacher views session in GitEnglishHub dashboard
2. Clicks "Curate" → verifies student speaker
3. Reviews pending words
4. Clicks "Send to Student" → commits to corpus

This ensures quality control over vocabulary entries.

---

## Related Documentation

For GitEnglishHub-side details (API routes, Sanity schemas, dashboard):

- See `gitenglishhub/ARCHITECTURE.md`

For session data format:

- See `DATA_STORAGE_GUIDE.md`

For keyboard controls during live sessions:

- See `CONTROLS.md`
