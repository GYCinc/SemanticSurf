# 🎯 Semantic Surfer - Features

## Native "Crimson Glass" UI ✨
- **Johnny Ive Aesthetic:** High-end glassmorphism with deep `blur-3xl` backgrounds and rounded `3xl` corners.
- **Tactile Depth:** Neomorphic shadow effects make cards feel like they are physically lifting off the screen.
- **High-Contrast Typography:** Optimized SF Pro and JetBrains Mono for perfect readability in dark environments.
- **Window Awareness:** Header padding respects macOS traffic lights for a native app experience.

## Live Metrics & Motion 🗣️
- **Velocity Tracking:** Real-time WPM (Words Per Minute) indicator with color-coded pacing feedback.
- **Smooth Motion:** Physics-based Framer Motion transitions for new turns and interactive elements.
- **Connection Heartbeat:** Live status indicator for WebSocket and AssemblyAI connectivity.

## Tiered Analysis Pipeline 📊
*Pure Python metrics ground the LLM to prevent hallucinations.*

### 1. Local Deterministic Tier
- **POS Tagging:** Analysis of noun/verb density and lexical complexity.
- **N-gram Naturalness:** Comparison of student bigrams against a native baseline.
- **Verb & Article Check:** Automated detection of tense inconsistencies and article (a/an) mismatches.
- **Personalized Benchmarking:** **Tutor Overlap %** measures how closely the student mirrors your own speech.

### 2. AI Gateway Tier
- **Models:** Gemini 1.5 Pro (Live Synthesis) / Claude 4.5 (Batch Processing).
- **Grounded Context:** The LLM receives session notes and hard Python metrics to ensure high-fidelity reporting.
- **CEFR Estimation:** Accurate proficiency leveling based on the SLA / CAF framework.

## Integrated Marking & Notes 📝
- **Granular Marking:** Click individual words for Vocabulary Gaps; click lines for Grammar/Expressions.
- **Immediate Sanity Sync:** Marked focus points are converted into Sanity Analysis Cards instantly.
- **Executive Summary:** Live notes sidebar captures real-time tutor observations for inclusion in the final report.

## High-Definition Diarization 👥
- **Dual-Pass Logic:** Real-time speaker labeling followed by a professional-grade **Batch Diarization** pass upon session end.
- **Audio Integrity:** Replaces rough streaming transcripts with high-quality, speaker-separated final cuts.

## Data Ecosystem ☁️
- **Unified Hub API:** One call (`ingest.createSession`) handles all backend routing to Supabase and Sanity.
- **Staging Workflow:** Student words are sent to the Hub Inbox for manual teacher curation (No auto-commit).
- **Local Backup:** Every session is cached locally in `sessions/` as a timestamped JSON file.

---

*Fast metrics + Deep AI intelligence. Grounded, accurate, and production-ready.*