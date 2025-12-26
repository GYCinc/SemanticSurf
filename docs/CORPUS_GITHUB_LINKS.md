# GitHub Corpus Resources Found

## Status: NONE OF THESE ARE INTEGRATED

**Current analyzers are custom MVPs - NOT the real implementations**

## Found Repositories

### 1. PELIC (Pittsburgh English Language Institute Corpus)

- **GitHub**: https://github.com/ELI-Data-Mining-Group/PELIC-dataset
- **Purpose**: Learner error patterns
- **Current Status**: NOT INTEGRATED - we have custom `learner_error_analyzer.py` with hardcoded regex

### 2. AMALGUM Corpus

- **GitHub**: https://github.com/gucorpling/amalgum
- **Purpose**: Register/genre analysis
- **Current Status**: NOT INTEGRATED - we have custom `amalgum_analyzer.py` with hardcoded word lists

### 3. PASTRIE Preposition Corpus

- **Source**: ACL Anthology / Georgetown University
- **Links**:
  - https://aclanthology.org/2020.law-1.10/
  - https://nert-nlp.github.io/pastrie/
- **Purpose**: Preposition error patterns
- **Current Status**: NOT INTEGRATED - we have custom `preposition_analyzer.py` with hardcoded patterns

### 4. Verb Transitivity Database

- **GitHub**: https://github.com/wilcoxeg/verb_transitivity
- **Data**: 7,965 English verbs with transitivity percentages from Google N-grams
- **Current Status**: NOT INTEGRATED - we have custom `verb_analyzer.py` with a small TSV file

### 5. Phonetic Corpora

- **TIMIT**: Standard speech corpus
- **L2-ARCTIC**: Non-native speech with mispronunciation annotations
- **Buckeye Corpus**: American English conversational speech
- **Current Status**: NOT INTEGRATED - we have custom `pronunciation_analyzer.py` with hardcoded patterns

### 6. N-gram Resources

- **Google Books N-gram Corpus**: Billions of n-grams
- **COCA N-grams**: 1 billion words
- **Current Status**: NOT INTEGRATED - we have custom `ngram_analyzer.py` with ~20 hardcoded bigrams

### 7. POS Tagging

- **Penn Treebank**: Standard POS tag set
- **Libraries**: NLTK already uses Penn Treebank tags
- **Current Status**: ACTUALLY INTEGRATED - `pos_analyzer.py` uses NLTK correctly

## What Needs to Happen

1. Download actual corpus data from these repos
2. Replace custom implementations with real data
3. Test each analyzer on REAL student data
4. Stop claiming things work without verification

## Current False Claims in Documentation

- Architecture.md claims all analyzers are "integrated" ✗ FALSE
- I claimed all analyzers "work" based on import tests ✗ MISLEADING
- I said tests "passed" without running real error detection ✗ FALSE
