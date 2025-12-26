# Semantic Server Architecture: The MiniGuru

## Overview
The Semantic Server (MiniGuru) is a precision desktop tool designed to act as a **Data Vacuum**. It captures raw ESL tutoring data (audio/text) and processes it through a deterministic linguistic suite before handing it off to the **Brain (GitEnglish Hub)** for long-term storage and pedagogical reasoning.

---

## 🏗️ The Triple-Transcript Bedrock
Every session creates local artifacts in `sessions/`:
1.  **`audio_[timestamp].wav`**: High-fidelity recording.
2.  **`upload_audio_aain_cache.json`**: Cached transcription and analysis data (Local backup).
3.  **The Live Feed**: WebSocket stream providing real-time WPM and transcript updates to the UI.

---

## 🛰️ System Components

### 1. The Ears (Real-time Engine)
*   **Component:** `main.py`
*   **Role:** Active Data Capture.
*   **Function:** Manages the AssemblyAI Streaming connection and local audio buffering. It broadcasts live events to the Electron UI via WebSockets (Port 8765).

### 2. The Vacuum (The MiniGuru)
*   **Component:** `semantic_server.py` (FastAPI)
*   **Role:** The Linguistic Filter & Local Analyst.
*   **Function:** Operates on Port 8080. It runs the deterministic analysis suite (CAF metrics, POS tagging, N-gram detection) using `analyzers/`. It synthesizes this data with LLM reasoning (Gemini 3 Flash) to produce a post-session report.

### 3. The Brain (GitEnglish Hub)
*   **Component:** Remote Hub API
*   **Role:** Final Human/AI Synthesis & Authority.
*   **Function:** The destination for all "vacuumed" data. The Hub manages student profiles, lifelong linguistic records (PCL), and teacher-approved lesson feedback.

---

## 📊 The Analysis Pipeline

### 1. Hard Numbers
*   Processes raw transcripts using `NLTK` and `TextBlob`.
*   **Metrics:** Complexity, Accuracy, Fluency (SLA Framework).
*   **Pattern Detection:** Hesitation markers, article/preposition errors, and formulaic sequences.

### 2. LLM Reasoning
*   Uses the **AssemblyAI LLM Gateway** (Gemini 3 Flash Preview).
*   Synthesizes the deterministic metrics with teacher notes and raw transcripts.
*   Outputs structured JSON feedback adhering to the `LanguageFeedback` schema.

---

## 🛠️ Tech Stack
*   **Ingestion:** Python `pyaudio` + `websockets` (Port 8765).
*   **Post-Session Analysis:** FastAPI (Port 8080).
*   **Transcription:** AssemblyAI (Streaming V3 & Batch).
*   **Intelligence:** Gemini 3 Flash Preview.
*   **Frontend:** Electron + Tailwind CSS.

---

*Refined for the Polyguru Ecosystem. Terminal Terminology: Data Vacuum (Local) -> Brain (Remote Hub).*
