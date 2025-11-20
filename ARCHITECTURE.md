# Semantic Surfer Architecture

## Overview
Semantic Surfer is a desktop application designed for ESL (English as a Second Language) tutors and students. It provides real-time transcription, speaker diarization, and AI-powered analysis of spoken language.

The system uses a **Hybrid Stack** architecture to ensure data integrity and flexibility:
1. **Supabase (PostgreSQL):** Stores the immutable, raw transcript stream.
2. **Sanity.io (Headless CMS):** Stores the mutable, AI-generated analysis cards (study material).
3. **Electron:** The desktop client that orchestrates the data flow.
4. **Python Backend:** Handles audio streaming and LLM processing.

---

## 1. Data Flow & The Hybrid Stack

### A. Raw Stream (The "Truth")
- **Source:** AssemblyAI Streaming API (v3)
- **Destination:** Supabase (`transcripts` table)
- **Characteristics:** Immutable, Append-Only.
- **Key Fields:** `session_id` (AssemblyAI UUID), `speaker` ("Aaron" or Student Name), `text`, `timestamp`, `metadata` (JSONB for words/pauses).
- **Purpose:** A permanent record of the session. Used for re-creation, deeper research, and corpus analysis.

### B. Analysis Cards (The "Study Material")
- **Source:** Electron Client (User Interaction + LLM)
- **Destination:** Sanity.io (`analysisCard` schema)
- **Characteristics:** Mutable, Curated.
- **Key Fields:** 
    - `category` (VOCAB_GAP, GRAMMAR_ERR, etc.)
    - `detectedTrigger` (What the student said)
    - `suggestedCorrection` (Better way to say it)
    - `explanation` (Why?)
    - `sourceReference` (Link to Supabase Session ID + Timestamp)
- **Purpose:** Flashcards, study guides, and review material for the student.

---

## 2. Core Components

### Python Backend (`main.py`)
- **Audio Streaming:** Captures microphone input (customizable device index) and streams to AssemblyAI.
- **WebSocket Server:** Broadcasts transcripts to the Electron frontend on `ws://localhost:8765`.
- **LLM Gateway:** Handles `analyze_turn` requests using `claude-3-5-haiku` via AssemblyAI's LLM Gateway.
- **Tool Calling:** Enforces structured JSON output from the LLM for consistent feedback cards.
- **Local Session Management:** Saves sessions to JSON files as a backup.

### Electron Frontend (`viewer2.html`, `electron-main.js`)
- **UI:** React-based real-time transcript viewer.
- **Visuals:** Staircase hover effects for focus.
- **Interaction:** 
    - **Click to Analyze:** Clicking a student bubble triggers the LLM.
    - **Numpad Shortcuts:** Keys 1-5 auto-categorize and analyze the *last* student turn.
- **Sanity Integration:** Uses `sanityClient.js` in the main process to securely save cards.

---

## 3. File Naming & Storage
To balance human readability with system traceability:

- **Local Filenames:** `sessions/{student_name}_session_{YYYY-MM-DD_HH-MM-SS}.json`
    - *Example:* `sessions/maria_session_2023-10-27_14-30-00.json`
    - easy to find by hand.
- **Internal ID:** The AssemblyAI Session ID (UUID) is stored **inside** the JSON file as the `session_id` field.
    - *Example:* `"session_id": "741efce3-7335-4946-bd12-d355e18c9802"`
    - Critical for linking Sanity cards back to the raw audio/transcript in Supabase.

---

## 4. Key Workflows

### Live Transcription & Diarization
1. **Audio Input:** Python captures audio.
2. **Diarization:** AssemblyAI labels speakers as 'A' (Tutor) or 'B' (Student).
3. **Mapping:** Backend maps 'A' -> "Aaron" (Configurable) and 'B' -> Current Student Profile.
4. **Display:** Frontend places Tutor on Right, Student on Left.

### AI Analysis (The "Click" or "Shortcut")
1. **Trigger:** User clicks a bubble OR presses Numpad 1-5.
2. **Request:** Frontend sends `analyze_turn` to Python backend.
3. **Context:** Backend grabs the target text + last 5 turns of context.
4. **LLM Processing:** `claude-3-5-haiku` analyzes the text for errors/improvements.
5. **Review:** Frontend displays a modal with the AI's suggestion.
6. **Save:** User edits and confirms -> Saved to Sanity.

---

## 5. Troubleshooting
- **"CSS Code" visible in Electron:** Usually means a syntax error in `viewer2.html` prevented React from mounting. Check the file for accidental pastes.
- **Supabase Schema Error:** If `metadata` column is missing, run the SQL fix and **reload the schema cache** (`NOTIFY pgrst, 'reload config';`).
- **Sanity Connection Error:** Check `.env` for `SANITY_PROJECT_ID` and `SANITY_API_TOKEN`.

