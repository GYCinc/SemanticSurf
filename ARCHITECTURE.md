# Semantic Surfer Architecture

## Overview
Semantic Surfer is a precision desktop application for real-time ESL tutoring. It captures audio, performs tiered linguistic analysis (Local Python + LLM Gateway), and delivers curated artifacts to the **GitEnglishHub** platform.

---

## 🏗️ Core Philosophy: "Happens" vs. "Exists"

- **Supabase (The Event Stream):** Stores what *happens*—raw transcripts, temporal turn-by-turn logs, and session metadata. This is your high-fidelity historical record.
- **Sanity (The Knowledge Base):** Stores what *exists*—curated Analysis Cards, marked Vocabulary Gaps, and Grammar Insights. These are the permanent pedagogical artifacts.

---

## 🔄 Unified Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SEMANTIC SURFER (Desktop)                      │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Audio Capture (High-Gain Mono Mic Stream)                        │
│ 2. Real-time AssemblyAI Transcription (v3 Streaming API)            │
│ 3. LIVE: WPM, Pauses, and Tutor Marks captured in Viewer UI         │
│ 4. ON SESSION END:                                                  │
│    a. High-Definition Batch Diarization (speaker_labels=True)       │
│    b. Local NLP Tier (POS, N-grams, Verbs, Comparative Ratios)      │
│    c. LLM Gateway Synthesis (Gemini 1.5 Pro + Full Data Context)     │
│ 5. Results → GitEnglishHub API (/api/mcp)                           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GITENGLISHHUB (API / Petty Dantic)             │
├─────────────────────────────────────────────────────────────────────┤
│ Centralized logic handler for the platform:                         │
│ - ingest.createSession → Supabase (The Log)                         │
│ - Analysis Cards → Sanity CMS (The Artifacts)                       │
│ - Corpus Staging → Hub Inbox (Awaiting Manual Curation)             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Tiered Analysis Pipeline

Semantic Surfer avoids hallucinations by grounding the LLM in deterministic local data.

### Phase 1: Local Deterministic Analyzers (Python)
*Calculated before the LLM call to provide hard grounding data.*

| Component | Logic | Output for LLM |
|-----------|-------|----------------|
| `POSAnalyzer` | TextBlob / NLTK | Raw counts and normalized ratios (Noun/Verb density). |
| `NgramAnalyzer` | Punctuation-stripped bigrams | Naturalness Score (grounded in native baseline). |
| `VerbAnalyzer` | Transitivity Lookup (14k verbs) | List of irregular verbs and usage probabilities. |
| `ArticleAnalyzer` | Phonetic rule matching | List of 'a/an' mismatches with phonetic explanations. |
| `Comparative` | Tutor vs. Student | **Tutor Overlap %** and Lexical Calibration ratio. |
| `Session` | SLA / CAF Framework | Complexity (MLT), Accuracy, and Fluency (WPM). |

### Phase 2: LLM Synthesis (LLM Gateway)
*The system prompt is dynamically injected with the results from Phase 1.*

- **Live Model:** `gemini-1.5-pro` (Optimized for speed/depth balance).
- **Batch Model:** `claude-sonnet-4-5` (Optimized for maximum linguistic depth).
- **Context Injection:** Raw Transcript + **Tutor Session Notes** + Phase 1 Context Bundle.
- **Output:** Structured JSON containing CEFR proficiency estimates and prioritized remedial tasks.

---

## 💻 System Components

### 1. Python Backend (`main.py`)
- Orchestrates the AssemblyAI stream and the local analysis suite.
- **ID Management:** Uses `session_id` throughout to align with AssemblyAI standards.
- **Egress:** `send_to_gitenglish()` is the sole point of contact for the Hub API.

### 2. Electron Frontend (`viewer2.html`)
- **Aesthetic:** "Crimson Glass" Edition—Johnny Ive inspired glassmorphism with neomorphic depth.
- **Interactions:** Word-level marking (Vocab Gap) and Turn-level marking (Grammar).
- **Lifting UI:** Staggered Framer Motion animations for high-fidelity responsiveness.

---

## 🛠️ Environment & Security

- `ASSEMBLYAI_API_KEY`: API authentication for all AI services.
- `MCP_SECRET`: Critical shared secret for GitEnglishHub API communication.
- `GITENGLISH_API_BASE`: Target URL for all unified data sync.

---

*This document is the authoritative blueprint for the Semantic Surfer system. Revision: Dec 2025.*
