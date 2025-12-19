# Semantic Surfer Data Pipeline
This document outlines the data flow from audio input to final storage.

## 1. Audio Ingestion (`main.py`)
*   **Source:** Microphone (Device Index from `config.json` or System Default).
*   **Capture:** `pyaudio` captures raw PCM audio (16-bit, 16kHz, Mono).
*   **Stream:** Audio is streamed via WebSocket to `streaming.assemblyai.com`.
*   **Backup:** Raw audio is simultaneously saved to `sessions/audio_[timestamp].wav`.

## 2. Transcription & Diarization (AssemblyAI)
*   **Service:** AssemblyAI Streaming API (v2/v3).
*   **Settings:**
    *   `punctuate=False`, `format_text=False` (Raw text for ESL accuracy).
    *   `encoding=pcm_s16le`.
*   **Events:**
    *   `Partial`: Interim results (not saved, optional UI display).
    *   `Final` (`end_of_turn=True`): Completed utterances.
*   **Diarization:** Returns Speaker "A", "B", etc.
    *   **Logic:** System maps these to "Speaker A" / "Speaker B" to preserve diarization integrity.

## 3. Session Processing (`main.py`)
*   **Storage:** `current_session` dictionary (in-memory).
*   **Turn Data:** Each final turn is processed:
    *   **Words:** Timestamp, confidence, text for each word.
    *   **Analysis:** WPM, pause duration, low confidence detection.
*   **Local Save:**
    *   File: `sessions/{StudentName}_session_{Timestamp}.json`
    *   Trigger: Every final turn, note update, or mark update.

## 4. User Interaction (`viewer2.html`)
*   **Display:** Receives transcript via WebSocket (`ws://localhost:8765`).
*   **Marking:**
    *   User clicks Word -> Copied to Clipboard + Added to "Marked Notes" + Saved to Session.
    *   User clicks Line -> Copied to Clipboard + Added to "Marked Notes" + Saved to Session.
    *   **Note:** These actions update the JSON file immediately.

## 5. Post-Session Pipeline (Unified Hub API)
*   **Trigger:** "END SESSION" button in `viewer2.html`.
*   **Sequence:**
    1.  **HD Diarization:** Batch processing via AssemblyAI Async API for precise speaker labeling.
    2.  **Local Analysis:** Execution of `POS`, `Ngram`, `Verb`, and `Comparative` analyzers.
    3.  **LLM Synthesis:** **Gemini 1.5 Pro** summarizes the session using full context (Transcript + Notes + Local Metrics).
    4.  **API Handoff:** A single payload is sent to `https://www.gitenglish.com/api/mcp` via `ingest.createSession`.
*   **Final Destination (Handled by Hub):**
    *   **Supabase:** Session logs and metadata.
    *   **Sanity:** Pedagogical artifacts (Analysis Cards).
    *   **Inbox:** Words/Terms staged for manual curation into the Student Corpus.
