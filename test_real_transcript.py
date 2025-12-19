#!/usr/bin/env python3
"""
Test analyzers on REAL dysfluent transcript data - not perfect sentences.

Based on SLA Transcript Analysis Framework examples.
This is what actual learner speech looks like.
"""

# REAL transcript excerpt from SLA Framework (Maria, Spanish L1,  2 years study)
REAL_TRANSCRIPT = """
Uhm... I go... I went to the park with my sister.
Is very beautiful park. The peoples there is very friendly.
Yes. Are very friendly. We... we see a man who... who have a amazing dog.
I don't know the name but is... was big and run very fast.
"""

print("="*60)
print("TESTING ON REAL DYSFLUENT TRANSCRIPT DATA")
print("="*60)
print(f"Transcript:\n{REAL_TRANSCRIPT}\n")

# Test each analyzer
from analyzers.article_analyzer import ArticleAnalyzer
from analyzers.preposition_analyzer import PrepositionAnalyzer
from analyzers.learner_error_analyzer import LearnerErrorAnalyzer
from analyzers.verb_analyzer import VerbAnalyzer
from analyzers.pos_analyzer import POSAnalyzer
from analyzers.phenomena_matcher import PhenomenaPatternMatcher
from analyzers.pronunciation_analyzer import PronunciationAnalyzer

print("\n1. ARTICLE ANALYZER (L1 Spanish Contrastive Analysis)")
print("-" * 40)
# Source: https://github.com/ELI-Data-Mining-Group/PELIC-dataset
article = ArticleAnalyzer()
results = article.analyze(REAL_TRANSCRIPT)
print(f"Found {len(results)} errors:")
for r in results:
    print(f"  - {r['item']}: {r['explanation']}")

print("\n2. PREPOSITION ANALYZER (PASTRIE Corpus Integration)")
print("-" * 40)
# Source: https://github.com/nert-nlp/pastrie
prep = PrepositionAnalyzer()
results = prep.analyze(REAL_TRANSCRIPT)
print(f"Found {len(results)} errors:")
for r in results:
    print(f"  - {r['item']}: {r['explanation']}")

print("\n3. LEARNER ERROR ANALYZER (PELIC-based)")
print("-" * 40)
learner = LearnerErrorAnalyzer()
results = learner.analyze(REAL_TRANSCRIPT)
print(f"Found {len(results)} errors:")
for r in results:
    print(f"  - {r['item']}: {r['explanation']}")

print("\n4. PHENOMENA MATCHER (5,000 Patterns from Treebank)")
print("-" * 40)
# Source: https://github.com/ELI-Data-Mining-Group/PELIC-dataset (Extrapolated via Treebank)
phen_matcher = PhenomenaPatternMatcher()
results = phen_matcher.match(REAL_TRANSCRIPT)
print(f"Found {len(results)} matches in your corpus:")
for r in results:
    print(f"  - [{r['item']}] in context: \"{r['context']}\"")
    print(f"    Source logic: {r['source']}")

print("\n5. VERB ANALYZER")
print("-" * 40)
verb = VerbAnalyzer()
from textblob import TextBlob
blob = TextBlob(REAL_TRANSCRIPT)
tags = list(blob.tags) if hasattr(blob, "tags") else []
print(f"Found {len(tags)} POS tags")
# Check for verbs
verbs_found = [word for word, tag in tags if tag.startswith('VB')]
print(f"Verbs in text: {verbs_found}")

print("\n6. PRONUNCIATION ANALYZER (FAE-CV Patterns)")
print("-" * 40)
# Source: FAE-CV (Foreign Accented English) Research Patterns
pron = PronunciationAnalyzer()
results = pron.analyze(REAL_TRANSCRIPT)
print(f"Found {len(results)} potential pronunciation-related patterns:")
for r in results:
    print(f"  - {r['item']}: {r['explanation']}")

print("\n7. POS ANALYZER (NLTK/Treebank Ratio)")
print("-" * 40)
# Source: https://github.com/sloria/TextBlob (NLTK Treebank)
pos = POSAnalyzer()
summary = pos.get_summary(REAL_TRANSCRIPT)
print(f"Verb Ratio: {summary['verb_ratio']:.2f}")
print(f"Noun Ratio: {summary['noun_ratio']:.2f}")
print(f"Adjective Ratio: {summary['adjective_ratio']:.2f}")

print("\n" + "="*60)
print("EXPECTED ERRORS IN THIS TRANSCRIPT:")
print("="*60)
print("""
1. Missing subject "It" before "is very beautiful park"
2. Wrong plural "peoples" (should be "people")  
3. Subject-verb agreement "peoples...is" (should be "are")
4. Verb tense "see" (should be "saw")
5. Subject-verb agreement "who have" (should be "has")
6. Article error "a amazing" (should be "an amazing")
7. Verb tense "run" (should be "ran")
""")
