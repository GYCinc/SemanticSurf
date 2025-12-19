# SLA Transcript Analysis Framework - Key Resources

## From the Academic Paper Citations

### Learner Corpora (The Gold Standard)

1. **PELIC (Pittsburgh English Language Institute Corpus)**

   - 4.2 million words from 1,100+ ESL students
   - Longitudinal data tracking learner development
   - Open access on GitHub
   - Link: https://github.com/ELI-Data-Mining-Group/PELIC-dataset
   - **STATUS**: NOT INTEGRATED

2. **SLABank / TalkBank**

   - Large databases of L2 learner transcripts
   - Works with CLAN analysis software
   - Link: https://slabank.talkbank.org/
   - **STATUS**: NOT INTEGRATED

3. **AMALGUM Corpus**

   - 4 million tokens across 8 genres
   - Register analysis (Academic vs Conversational)
   - GitHub: https://github.com/gucorpling/amalgum
   - **STATUS**: NOT INTEGRATED

4. **PASTRIE Preposition Corpus**
   - Reddit data with preposition supersense tags
   - Tracks L1 influence on L2 preposition usage
   - ACL Anthology: https://aclanthology.org/2020.law-1.10/
   - Georgetown: https://nert-nlp.github.io/pastrie/
   - **STATUS**: NOT INTEGRATED

### Analysis Tools (From Paper)

5. **CLAN (Computerized Language Analysis)**

   - Calculates MLU, TTR, frequency counts
   - Works with CHAT format transcripts
   - TalkBank: https://talkbank.org/clan/
   - **STATUS**: NOT INSTALLED

6. **ELAN (EUDICO Linguistic Annotator)**

   - Time-aligned multimedia annotation
   - Essential for fluency metrics (pause duration, articulation rate)
   - Max Planck Institute: https://archive.mpi.nl/tla/elan
   - **STATUS**: NOT INSTALLED

7. **AntConc (Corpus Analysis Toolkit)**
   - Concordance, n-grams, keyword analysis
   - Free: https://www.laurenceanthony.net/software/antconc/
   - **STATUS**: NOT INSTALLED

### Lexical/Verb Resources

8. **VerbNet**

   - Verb classifications by semantics & syntax
   - Link: https://verbs.colorado.edu/verbnet/
   - **STATUS**: NOT INTEGRATED

9. **PropBank**

   - Verb argument structure annotations
   - Link: https://propbank.github.io/
   - **STATUS**: NOT INTEGRATED

10. **WordNet**

    - Lexical database (synsets, relations)
    - NLTK includes this - WE ALREADY USE IT
    - **STATUS**: ✓ INTEGRATED (via NLTK)

11. **Google Syntactic N-grams**

    - Dependency tree fragments from Google Books
    - Link: https://storage.googleapis.com/books/syntactic-ngrams/index.html
    - **STATUS**: NOT INTEGRATED

12. **Verb Transitivity Database (wilcoxeg)**
    - 7,965 verbs with transitivity percentages
    - GitHub: https://github.com/wilcoxeg/verb_transitivity
    - **STATUS**: Partially integrated (small TSV only)

### Speech/Pronunciation Corpora

13. **TIMIT Corpus**

    - 630 speakers, 8 dialects, phonetic transcriptions
    - LDC: https://catalog.ldc.upenn.edu/LDC93S1
    - **STATUS**: NOT INTEGRATED

14. **L2-ARCTIC**

    - Non-native English with mispronunciation annotations
    - UCI: https://psi.engr.tamu.edu/l2-arctic-corpus/
    - **STATUS**: NOT INTEGRATED

15. **Buckeye Corpus**
    - 300k words, time-aligned American English
    - Ohio State: https://buckeyecorpus.osu.edu/
    - **STATUS**: NOT INTEGRATED

## What We Actually Have

- ✓ NLTK with Penn Treebank POS tags (working)
- ✓ TextBlob for basic NLP (working)
- ✗ 9 custom "stub" analyzers with hardcoded patterns (NOT real corpus data)
- ✗ Pattern matcher with 5,074 patterns (needs validation on real transcripts)

## What Needs to Happen (Prioritized)

### Phase 1: Get Real Error Detection Working

1. Download PELIC dataset → extract common ESL error patterns
2. Download PASTRIE → replace preposition analyzer patterns
3. Download verb_transitivity full dataset → replace our 400-verb TSV
4. Test ALL analyzers on REAL dysfluent transcript (like the test I just ran)

### Phase 2: Add Missing Analysis Dimensions

5. Install CLAN → calculate MLU, TTR properly
6. Implement CAF metrics (Complexity/Accuracy/Fluency from paper)
7. Add error classification (interlingual vs intralingual)

### Phase 3: Speech-Specific Features

8. Integrate L2-ARCTIC pronunciation patterns
9. Add pause analysis (breakdown fluency)
10. Add repair/dysfluency detection

## Test Results Summary (REAL Transcript)

**Expected Errors**: 7
**Detected Errors**: 1 (Article Analyzer only)
**Detection Rate**: 14%

### What We Missed:

- Missing subject pronoun detection: 0/1
- Plural form errors ("peoples"): 0/1
- Subject-verb agreement: 0/2
- Verb tense errors: 0/2
- Total misses: 6/7

**CONCLUSION**: Current analyzers are MVPs that don't work on real learner data.
