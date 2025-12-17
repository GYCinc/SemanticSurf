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
│ 3. LLM Gateway (Claude/Gemini) analyzes linguistic phenomena        │
│ 4. Results → Petty Dantic API (GitEnglishHub)                       │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GITENGLISHHUB                                   │
│             https://www.gitenglish.com                               │
├─────────────────────────────────────────────────────────────────────┤
│ POST /api/mcp  →  Petty Dantic Action Registry                      │
│ - ingest.createSession → student_sessions table (STAGING)           │
│ - corpus.validateAndStore → student_corpus table (APPROVED ONLY)    │
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

**CRITICAL: Session Lifecycle Requirements**

1. **Session MUST be properly ended** via the "END SESSION" button in the UI
2. If session is not properly ended:
   - Audio file will be 0 bytes (wave file never closed)
   - Batch diarization cannot run (requires audio file)
   - Speaker identification will not occur
   - `diarized_turns` will be empty
   - Data cannot flow to GitEnglishHub corpus
3. The `MonoMicrophoneStream.close()` method closes the wave file
4. The `on_terminated` callback runs batch diarization and uploads to GitEnglishHub

### Method 2: Pre-Recorded Script (`ingest_audio.py`)

Batch processing for recorded lessons.

```bash
python ingest_audio.py
```

- Dual-pass transcription (raw + diarized)
- LLM Gateway analysis extracts linguistic phenomena
- Creates session and stages for Inbox approval

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
- LLM Gateway analysis with linguistic prompt (Claude Sonnet 4.5)
- Stages sessions for teacher approval in GitEnglishHub Inbox

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

## NLP Analysis: LLM Gateway (Migrated from LeMUR)

**IMPORTANT: LeMUR ≠ LLM Gateway**

Although both are AssemblyAI products for AI analysis, they are **fundamentally different systems**:

### LeMUR (Legacy)

- **SDK-based**: Uses `assemblyai` Python SDK (`aai.Lemur().task()`)
- **Limited models**: Restricted to models in the SDK's enum (Anthropic, Mistral only in v0.48.1)
- **Automatic transcript fetch**: Automatically retrieves transcript via transcript ID
- **Simple response**: Returns `.response` attribute with analysis text
- **Model names**: Enum-based (e.g., `aai.LemurModel.claude_sonnet`)

### LLM Gateway (Current)

- **HTTP-based**: Direct POST to `https://llm-gateway.assemblyai.com/v1/chat/completions`
- **Broader model support**: Claude, GPT, **and Gemini models** (not available in LeMUR SDK)
- **Manual transcript inclusion**: Must include transcript text in request payload
- **OpenAI-compatible format**: Returns standard chat completion response
- **Model names**: String-based (e.g., `"claude-sonnet-4-5-20250929"`, `"gemini-3-pro-preview"`)

### Why We Migrated

1. **Model Access**: LeMUR SDK v0.48.1 doesn't recognize newer models like Gemini 3.0
2. **Future-Proofing**: LLM Gateway is the modern API with ongoing model additions
3. **Flexibility**: Direct HTTP calls allow custom request handling

### Current Configuration

**File**: `ingest_audio.py` (as of Dec 2025)
**Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
**Endpoint**: `https://llm-gateway.assemblyai.com/v1/chat/completions`
**Max Tokens**: 8000

### Analysis Output

The LLM Gateway analyzes transcripts for:

1. **Annotated Errors** - Quote, correction, category, explanation
2. **Student Profile** - CEFR estimate, dominant issue
3. **Prioritized Tasks** - HIGH/MEDIUM/LOW remedial activities

Categories: Syntax, Lexis, Pragmatics

---

## Corpus Commitment Flow

Words are NOT auto-committed. Human curation required.

### Data Source: AssemblyAI Word-Level Transcript

The corpus uses **AssemblyAI's word-for-word transcript** with full metadata:

```json
{
  "text": "running",
  "start": 1234,
  "end": 1567,
  "confidence": 0.98,
  "speaker": "A"
}
```

This is stored in `session.metrics.pending_words` after transcription.

### Flow

```
AssemblyAI Transcription
    ↓
Words saved to session metrics (pending_words)
    ↓
Session appears in GitEnglishHub admin feed
    ↓
Teacher clicks "Curate" → verifies student speaker label
    ↓
Reviews pending words (can exclude specific words)
    ↓
Clicks "Send to Student" → POST /api/admin/sessions/commit-corpus
    ↓
Words filtered by selected speaker → inserted to student_corpus table
```

### Why Not Auto-Commit?

1. **Speaker verification** - Must confirm which speaker is the student
2. **Quality control** - Exclude filler words, false starts, unintelligible speech
3. **Context** - Teacher can add notes for specific vocabulary items

### Corpus Table Schema (`student_corpus`)

| Column       | Type      | Description                 |
| ------------ | --------- | --------------------------- |
| `id`         | uuid      | Primary key                 |
| `student_id` | uuid      | FK to students              |
| `session_id` | uuid      | FK to student_sessions      |
| `word`       | text      | The word/phrase             |
| `start_ms`   | int       | Start timestamp in audio    |
| `end_ms`     | int       | End timestamp in audio      |
| `confidence` | float     | AssemblyAI confidence (0-1) |
| `context`    | text      | Surrounding text (optional) |
| `created_at` | timestamp | When committed              |

This ensures quality control over vocabulary entries.

---

## Related Documentation

For GitEnglishHub-side details (API routes, Sanity schemas, dashboard):

- See `gitenglishhub/ARCHITECTURE.md`

For session data format:

- See `DATA_STORAGE_GUIDE.md`

For keyboard controls during live sessions:

- See `CONTROLS.md`

---

# Session Analysis Pipeline

> **See `gitenglishhub/ARCHITECTURE.md` for the Master Definition of the Pipeline.**

> **Last Updated:** 2025-12-16
> **Status:** STRICT ALIGNMENT with GitEnglishHub

## What Gets Analyzed

When a recording session ends, the following analysis chain executes **automatically**:

```
Audio Recording (main.py)
    ↓
AssemblyAI Transcription + Diarization
    ↓
SessionAnalyzer (analyzers/session_analyzer.py)
    ↓
LeMUR Query (analyzers/lemur_query.py)
    ↓
Results → Supabase + Session JSON
```

---

## SessionAnalyzer (`analyzers/session_analyzer.py`)

**Triggered by:** `main.py` line ~1133 after session ends

**Input:** Session JSON file with `turns`, `speaker_map`, `student_name`

### Basic Metrics (Always Run)

| Metric                | Description                                     | Method                          |
| --------------------- | ----------------------------------------------- | ------------------------------- |
| `speaking_rate`       | WPM analysis per turn                           | `analyze_speaking_rate()`       |
| `pauses`              | Pause count, duration, long pauses >1s          | `analyze_pauses()`              |
| `complexity_basic`    | Total words, unique words, vocabulary diversity | `analyze_complexity()`          |
| `vocabulary_analysis` | Lemma counts, overlap with teacher              | `analyze_vocabulary()`          |
| `fillers`             | um, uh, like, you know, so, well, actually      | `analyze_fillers()`             |
| `hesitation_patterns` | Words that precede long pauses (>800ms)         | `analyze_hesitation_patterns()` |

### Advanced Metrics (TextBlob)

| Metric                   | Description                           | Method                    |
| ------------------------ | ------------------------------------- | ------------------------- |
| `sentiment_polarity`     | -1.0 to 1.0 (negative to positive)    | `run_textblob_analysis()` |
| `sentiment_subjectivity` | 0.0 to 1.0 (objective to opinionated) | `run_textblob_analysis()` |
| `top_noun_phrases`       | Key topics discussed                  | `run_textblob_analysis()` |

### SLA Framework Metrics (NLTK)

| Metric           | Description                                     | Method               |
| ---------------- | ----------------------------------------------- | -------------------- |
| `ngram_analysis` | Bigrams, trigrams, 4-grams, formulaic sequences | `analyze_ngrams()`   |
| `pos_analysis`   | Penn Treebank POS tags, lexical density         | `analyze_pos_tags()` |
| `caf_metrics`    | Complexity, Accuracy, Fluency (MLT, C/T, MLR)   | `analyze_caf()`      |

---

## N-Gram Analysis (`analyze_ngrams`)

**What it does:** Identifies repeated word sequences (collocations, formulaic language)

**Output:**

```json
{
  "bigrams": [{"phrase": "I think", "count": 5}, ...],
  "trigrams": [{"phrase": "I don't know", "count": 3}, ...],
  "fourgrams": [{"phrase": "you know what I", "count": 2}, ...],
  "formulaic_sequences": [{"phrase": "I think", "count": 5, "length": 2}, ...]
}
```

**Why it matters:**

- Formulaic sequences (repeated 3+ times) indicate automatized language chunks
- These are acquisition targets - student has internalized these patterns
- Absence of common formulaic language suggests area for instruction

---

## POS Tag Analysis (`analyze_pos_tags`)

**What it does:** Penn Treebank tagging + WordNet lemmatization

**Penn Treebank Tags Used:**
| Tag | Category | Examples |
|-----|----------|----------|
| NN, NNS, NNP, NNPS | Nouns | dog, dogs, London, Alps |
| VB, VBD, VBG, VBN, VBP, VBZ | Verbs | run, ran, running, run, runs, runs |
| JJ, JJR, JJS | Adjectives | big, bigger, biggest |
| RB, RBR, RBS | Adverbs | quickly, more quickly, most quickly |
| IN | Prepositions | in, on, at, with |
| DT | Determiners | the, a, an |
| PRP, PRP$, WP | Pronouns | I, my, who |

**Output:**

```json
{
  "pos_distribution": {"NN": 45, "VB": 23, "JJ": 12, ...},
  "counts_by_category": {"nouns": 45, "verbs": 23, ...},
  "unique_by_category": {"nouns": ["dog", "house", ...], ...},
  "total_unique_lemmas": 87,
  "lexical_density": 0.52,
  "content_word_ratio": "80/154"
}
```

**WordNet Lemmatization:**

- Converts inflected forms to base form WITH correct POS
- "running" (VBG) → "run" (verb)
- "running" (NN) → "running" (noun, as in "running is fun")
- This is MORE ACCURATE than TextBlob's default lemmatization

**Lexical Density:**

- Formula: `(nouns + verbs + adjectives + adverbs) / total_words`
- Higher = more informationally dense speech
- Academic/formal speech: 0.5-0.6
- Casual conversation: 0.4-0.5

---

## CAF Metrics (`analyze_caf`)

**What it does:** Complexity, Accuracy, Fluency - the standard SLA proficiency triad

### Complexity

| Metric                     | Formula                                   | Interpretation                  |
| -------------------------- | ----------------------------------------- | ------------------------------- |
| `mean_length_t_unit` (MLT) | total_words / t_units                     | Higher = more complex sentences |
| `clauses_per_t_unit` (C/T) | (t_units + subordinate_clauses) / t_units | Higher = more subordination     |

**T-unit:** Main clause + any attached subordinate clauses  
_Approximation:_ Sentences split by `.!?`

**Subordinate clause markers detected:**
that, which, who, whom, whose, when, where, while, because, although, if, unless, since, after, before

### Fluency

| Metric                  | Formula                        | Interpretation                           |
| ----------------------- | ------------------------------ | ---------------------------------------- |
| `mean_length_run` (MLR) | total_words / (pauses + 1)     | Higher = longer stretches between pauses |
| `filled_pause_rate`     | (fillers / total_words) \* 100 | Lower = more fluent                      |

### Accuracy (Approximation)

| Metric                   | Detection Method                          | Interpretation         |
| ------------------------ | ----------------------------------------- | ---------------------- |
| `error_free_t_units_pct` | T-units without false starts or fragments | Higher = more accurate |
| `false_starts_detected`  | Repeated words (e.g., "I I went")         | Repair attempts        |
| `fragments_detected`     | T-units with <3 words                     | Incomplete utterances  |

> **Note:** True accuracy requires human annotation. This is a heuristic approximation.

---

## LeMUR Analysis (`analyzers/lemur_query.py`)

**Triggered by:** `main.py` line ~1264 after SessionAnalyzer

**What it does:** Uses AssemblyAI's LeMUR (Claude 3 Haiku) for linguistic analysis

### Default Prompt (from code)

```
As an expert ESL tutor, analyze the student's spoken English from this conversation.
Focus strictly on observable linguistic phenomena relevant to language acquisition.
Identify specific areas of strength and weakness in grammar, vocabulary, pronunciation,
fluency (pauses, rate, fillers), and discourse coherence.
Provide concrete examples from the transcript.
DO NOT generate metaphorical language, philosophical interpretations,
or content unrelated to ESL teaching and learning.
Avoid any "hippie-like", abstract, or non-academic terminology.
Present findings clearly and concisely, directly referencing the student's language use.
```

### Custom Prompt Support

Teachers can set a custom `lemur_prompt` in the session data to override the default.
This is stored in `session.lemur_prompt` and passed to the analysis.

### How It's Called

```python
lemur = aai.Lemur()
result = lemur.task(
    prompt=full_lemur_prompt,
    final_model='anthropic/claude-3-haiku',
    input_text=input_text  # Full conversation transcript
)
```

### Output

Returns `lemur_analysis` object with:

- `response`: The LLM's analysis text
- `request_id`: AssemblyAI request ID for debugging
- `usage`: Token usage stats

### Category Mapping (Done in GitEnglishHub)

The raw LeMUR response is parsed by GitEnglishHub and mapped to 6 public categories:

| LeMUR Finding           | Maps To                |
| ----------------------- | ---------------------- |
| Pronunciation patterns  | Fluency & Flow         |
| Discourse/turn-taking   | Fluency & Flow         |
| Grammar errors          | Grammar                |
| Vocabulary gaps         | Vocabulary             |
| "phrasal verb" mentions | Phrasal Verbs          |
| "collocation" mentions  | Collocations           |
| "idiom" mentions        | Idioms & Fixed Phrases |

---

## Dependencies

### Python Packages

```
textblob      # Sentiment, noun phrases, basic lemmatization
nltk          # POS tagging, WordNet, n-grams
assemblyai    # Transcription, LeMUR
supabase      # Database
```

### NLTK Data (Auto-downloaded)

```
punkt                          # Tokenization
averaged_perceptron_tagger     # POS tagging
averaged_perceptron_tagger_eng # English POS model
wordnet                        # Lemmatization dictionary
```

---

## Session JSON Structure

```json
{
  "session_id": "uuid",
  "student_name": "Maria",
  "speaker_map": {"A": "Maria", "B": "Aaron"},
  "turns": [...],
  "diarized_turns": [...],
  "metrics": {
    "student_metrics": {...},
    "caf_metrics": {...},
    "ngram_analysis": {...},
    "pos_analysis": {...},
    "lemur_analysis": {...}
  }
}
```

---

## Interpreting Results

### CEFR Level Estimation (from CAF)

| Level | MLT  | C/T     | Lexical Density | Typical Pattern                             |
| ----- | ---- | ------- | --------------- | ------------------------------------------- |
| A1-A2 | 4-6  | 1.0-1.1 | 0.35-0.45       | Simple sentences, limited vocabulary        |
| B1    | 6-8  | 1.1-1.3 | 0.45-0.50       | Compound sentences, formulaic chunks        |
| B2    | 8-12 | 1.3-1.5 | 0.50-0.55       | Complex sentences, varied vocabulary        |
| C1+   | 12+  | 1.5+    | 0.55+           | Sophisticated subordination, academic lexis |

### Red Flags to Watch

| Metric                  | Red Flag Value   | Indicates                       |
| ----------------------- | ---------------- | ------------------------------- |
| `filled_pause_rate`     | >5.0             | Excessive hesitation            |
| `false_starts_detected` | >3 per 100 words | Planning issues                 |
| `lexical_density`       | <0.35            | Over-reliance on function words |
| `mean_length_run`       | <5               | Frequent breakdown              |
| `clauses_per_t_unit`    | <1.0             | Only simple sentences           |

---

## Extending the Analysis

To add a new analysis method:

1. Add method to `SessionAnalyzer` class
2. Add call in `analyze_all()` student_metrics dict
3. Ensure graceful fallback if dependency unavailable
4. Document in this file

Example skeleton:

```python
def analyze_new_feature(self, text: str) -> Dict[str, Any]:
    """
    Description of what this analyzes.
    """
    if not REQUIRED_LIB_AVAILABLE or not text:
        return {'error': 'Library not available or no text'}

    try:
        # Analysis logic here
        return {'result': value}
    except Exception as e:
        logger.error(f"New feature analysis failed: {e}")
        return {'error': str(e)}
```

---

## References

- SLA Framework: `LEXICAL RESOURCES/SLA Transcript Analysis Framework.txt` (in gitenglishhub)
- Penn Treebank: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
- CEFR Levels: https://www.coe.int/en/web/common-european-framework-reference-languages
- CAF Research: Housen & Kuiken (2009) - Complexity, Accuracy, Fluency
