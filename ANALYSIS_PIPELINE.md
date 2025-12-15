# Session Analysis Pipeline

> **Last Updated:** 2025-12-15  
> **Location:** `/Users/safeSpacesBro/AssemblyAIv2`

## Overview

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

## What Gets Analyzed

### 1. SessionAnalyzer (`analyzers/session_analyzer.py`)

**Triggered by:** `main.py` line ~1133 after session ends

**Input:** Session JSON file with `turns`, `speaker_map`, `student_name`

**Output:** Analysis dict added to session metrics

#### Basic Metrics (Always Run)

| Metric                | Description                                     | Method                          |
| --------------------- | ----------------------------------------------- | ------------------------------- |
| `speaking_rate`       | WPM analysis per turn                           | `analyze_speaking_rate()`       |
| `pauses`              | Pause count, duration, long pauses >1s          | `analyze_pauses()`              |
| `complexity_basic`    | Total words, unique words, vocabulary diversity | `analyze_complexity()`          |
| `vocabulary_analysis` | Lemma counts, overlap with teacher              | `analyze_vocabulary()`          |
| `fillers`             | um, uh, like, you know, so, well, actually      | `analyze_fillers()`             |
| `hesitation_patterns` | Words that precede long pauses (>800ms)         | `analyze_hesitation_patterns()` |

#### Advanced Metrics (TextBlob)

| Metric                   | Description                           | Method                    |
| ------------------------ | ------------------------------------- | ------------------------- |
| `sentiment_polarity`     | -1.0 to 1.0 (negative to positive)    | `run_textblob_analysis()` |
| `sentiment_subjectivity` | 0.0 to 1.0 (objective to opinionated) | `run_textblob_analysis()` |
| `top_noun_phrases`       | Key topics discussed                  | `run_textblob_analysis()` |

#### SLA Framework Metrics (NLTK) - NEW

| Metric           | Description                                     | Method               |
| ---------------- | ----------------------------------------------- | -------------------- |
| `ngram_analysis` | Bigrams, trigrams, 4-grams, formulaic sequences | `analyze_ngrams()`   |
| `pos_analysis`   | Penn Treebank POS tags, lexical density         | `analyze_pos_tags()` |
| `caf_metrics`    | Complexity, Accuracy, Fluency (MLT, C/T, MLR)   | `analyze_caf()`      |

---

### 2. N-Gram Analysis (`analyze_ngrams`)

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

### 3. POS Tag Analysis (`analyze_pos_tags`)

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

### 4. CAF Metrics (`analyze_caf`)

**What it does:** Complexity, Accuracy, Fluency - the standard SLA proficiency triad

#### Complexity

| Metric                     | Formula                                   | Interpretation                  |
| -------------------------- | ----------------------------------------- | ------------------------------- |
| `mean_length_t_unit` (MLT) | total_words / t_units                     | Higher = more complex sentences |
| `clauses_per_t_unit` (C/T) | (t_units + subordinate_clauses) / t_units | Higher = more subordination     |

**T-unit:** Main clause + any attached subordinate clauses  
_Approximation:_ Sentences split by `.!?`

**Subordinate clause markers detected:**
that, which, who, whom, whose, when, where, while, because, although, if, unless, since, after, before

#### Fluency

| Metric                  | Formula                        | Interpretation                           |
| ----------------------- | ------------------------------ | ---------------------------------------- |
| `mean_length_run` (MLR) | total_words / (pauses + 1)     | Higher = longer stretches between pauses |
| `filled_pause_rate`     | (fillers / total_words) \* 100 | Lower = more fluent                      |

#### Accuracy (Approximation)

| Metric                   | Detection Method                          | Interpretation         |
| ------------------------ | ----------------------------------------- | ---------------------- |
| `error_free_t_units_pct` | T-units without false starts or fragments | Higher = more accurate |
| `false_starts_detected`  | Repeated words (e.g., "I I went")         | Repair attempts        |
| `fragments_detected`     | T-units with <3 words                     | Incomplete utterances  |

> **Note:** True accuracy requires human annotation. This is a heuristic approximation.

---

### 5. LeMUR Analysis (`analyzers/lemur_query.py`)

**Triggered by:** `main.py` line ~1264 after SessionAnalyzer

**What it does:** Uses AssemblyAI's LeMUR (Claude 3 Haiku) for linguistic analysis

**Prompt (4-domain analysis):**

```
Analyze these 4 linguistic domains:
1. Phonology (Pronunciation, intonation, connected speech)
2. Lexis (Vocabulary range, collocations, idiomatic usage)
3. Syntax (Grammar accuracy, sentence complexity, morphology)
4. Pragmatics (Discourse coherence, register, turn-taking)
```

**Output mapping to 6 public categories:**
| LeMUR Domain | Maps To |
|--------------|---------|
| Phonology | Fluency & Flow |
| Pragmatics | Fluency & Flow |
| Syntax | Grammar |
| Lexis (default) | Vocabulary |
| Lexis + "phrasal verb" | Phrasal Verbs |
| Lexis + "collocation" | Collocations |
| Lexis + "idiom" | Idioms & Fixed Phrases |

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

## Data Flow

```
Session Recording
       ↓
┌──────────────────────────────────────────────────────┐
│  main.py: on_session_end()                           │
│  - Saves session JSON to /sessions/                  │
│  - Calls analyze_session_file()                      │
│  - Calls run_lemur_query()                           │
│  - Uploads to Supabase student_sessions              │
│  - Populates student_corpus table                    │
└──────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────┐
│  Session JSON structure:                             │
│  {                                                   │
│    "session_id": "uuid",                             │
│    "student_name": "Maria",                          │
│    "speaker_map": {"A": "Maria", "B": "Aaron"},      │
│    "turns": [...],                                   │
│    "diarized_turns": [...],                          │
│    "metrics": {                                      │
│      "student_metrics": {...},                       │
│      "caf_metrics": {...},                           │
│      "ngram_analysis": {...},                        │
│      "pos_analysis": {...},                          │
│      "lemur_analysis": {...}                         │
│    }                                                 │
│  }                                                   │
└──────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────┐
│  Supabase Tables:                                    │
│  - student_sessions: Full session with metrics       │
│  - student_corpus: Individual words (after curation) │
│  - students: Student profiles                        │
└──────────────────────────────────────────────────────┘
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

- SLA Framework: `LEXICAL RESOURCES/SLA Transcript Analysis Framework.txt`
- Penn Treebank: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
- CEFR Levels: https://www.coe.int/en/web/common-european-framework-reference-languages
- CAF Research: Housen & Kuiken (2009) - Complexity, Accuracy, Fluency
