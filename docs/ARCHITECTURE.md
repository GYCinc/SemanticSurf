# Semantic Server Architecture: Multi-Instance Edition

## Overview
Semantic Server is a precision desktop tool for capturing raw ESL tutoring data. It operates within a "Multi-Instance" ecosystem: Local data capture (The CaptureEngine) feeds into Student-Isolated AI Instances (The Personal MiniGurus) hosted on Railway.

---

## 🏗️ The Triple-Transcript Bedrock
Every session creates three local artifacts in `sessions/[session_id]/`:
1.  **`_raw.txt`**: The conversation as it happened.
2.  **`_sentences.json`**: Diarized sentence segments.
3.  **`_words.json`**: The **Authoritative** word array (Timing, Confidence, Speaker).

---

## 🏰 The "Multi-Instance" Protocol (Personal Instances)
- **Isolation:** Every student is assigned a dedicated AI Instance (Service) on Railway.
- **Identity:** Instances are student-bound via environment variables (e.g., `STUDENT_ID`). 
- **Contamination Zero:** Memory and local state are never shared between student instances.
- **Scaling:** One "Master Blueprint" container is copied (replicated) for each new instance.

---

## 📊 The Analysis Pipeline

### 1. The Hard Numbers (Local Analysis)
*   **Component:** `SessionAnalyzer` (`analyzers/session_analyzer.py`)
*   **Role:** The Objective Statistician.
*   **Function:** Runs *before* any AI involvement. It processes the raw transcripts using `NLTK` and `TextBlob` to generate:
    *   **CAF Metrics:** Complexity, Accuracy, Fluency (SLA Framework).
    *   **Vocabulary Stats:** Unique lemmas, lexical density, content word ratio.
    *   **Pattern Detection:** N-grams (formulaic sequences), pauses, and hesitation markers.
    *   **Comparatives:** Student vs. Teacher talk time, WPM, and vocabulary overlap.

### 2. The Cognitive Layer (Distillation)
*   **Component:** `The Guru` (`analyzers/lm_gateway.py`)
*   **Role:** The Subjective Coach.
*   **Function:** Synthesizes the "Hard Numbers" and the raw transcript using the `UNIVERSAL_GURU_PROMPT.txt`.
*   **Output:** Generates qualitative feedback, identifies "Action Items," and flags "Marked Expressions" for review.

### 3. The Enforcer (Validation)
*   **Component:** `Petty Dantic` (`analyzers/schemas.py`)
*   **Role:** The Bureaucrat.
*   **Function:** Ensures all data leaving the Server adheres to the "Holy Schema." 
*   **The Hub Gateway:** Data is received via `/api/mcp` and published via the Admin Gateway (`/api/admin/sessions/curate`).

---

## 🔄 The Personal Language Corpus (PCL)
- **Engine:** `StudentCorpusEngine` counts student production from `_words.json`.
- **Bedrock (Supabase):** The `word_exposure` table stores the student's lifelong linguistic record.
- **Protocol:** Session words are staged in Supabase. Permanent commitment to `student_corpus` and delivery to the Student Inbox (Sanity) happens via the **Petty Dantic Gateway** after human review.

---

## 🛠️ Tech Stack & Dependencies
*   **Ingestion:** Python `pyaudio` + `websockets` (Local).
*   **Transcription:** AssemblyAI (Streaming & Batch).
*   **Server:** FastAPI (`semantic_server.py`) on Railway.
*   **Intelligence:** Gemini 1.5 Pro (via OpenRouter/Gateway).
*   **Storage:** Supabase (PostgreSQL).
*   **NLP:** NLTK, TextBlob.

---

*Authored by The Manager. Definitive Blueprint for the Multi-Instance Pipeline.*