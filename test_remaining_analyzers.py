#!/usr/bin/env python3
"""Test remaining analyzers 4-10 on real transcript data"""

import sys
sys.path.insert(0, '/Users/safeSpacesBro/AssemblyAIv2')

# Load real student text
with open('/tmp/student.txt', 'r') as f:
    text = f.read()

print("Testing on 300-word real transcript")
print("=" * 60)

# Test 4: Article Analyzer
print("\n4. Article Analyzer")
try:
    from analyzers.article_analyzer import ArticleAnalyzer
    analyzer = ArticleAnalyzer()
    result = analyzer.analyze(text)
    print(f"   Result: {result}")
    print(f"   Status: ✓ LOADS")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")

# Test 5: Preposition Analyzer
print("\n5. Preposition Analyzer")
try:
    from analyzers.preposition_analyzer import PrepositionAnalyzer
    analyzer = PrepositionAnalyzer()
    result = analyzer.analyze(text)
    print(f"   Result: {result}")
    print(f"   Status: ✓ LOADS")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")

# Test 6: POS Analyzer
print("\n6. POS Analyzer")
try:
    from analyzers.pos_analyzer import POSAnalyzer
    analyzer = POSAnalyzer()
    result = analyzer.analyze(text[:100])  # First 100 chars
    print(f"   Verb ratio: {result.get('verb_ratio', 'N/A')}")
    print(f"   Noun ratio: {result.get('noun_ratio', 'N/A')}")
    print(f"   Status: ✓ WORKS")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")

# Test 7: N-gram Analyzer
print("\n7. N-gram Analyzer")
try:
    from analyzers.ngram_analyzer import NgramAnalyzer
    analyzer = NgramAnalyzer()
    result = analyzer.analyze(text[:100])
    unusual_pct = result.get('unusual_bigram_count', 0) / max(result.get('total_bigrams', 1), 1) * 100
    print(f"   Unusual: {unusual_pct:.0f}%")
    print(f"   Status: {'✓ WORKS' if unusual_pct < 50 else '✗ TOO MANY UNUSUAL'}")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")


# Test 8: Comparative Analyzer
print("\n8. Comparative Analyzer")
try:
    from analyzers.comparative_analyzer import ComparativeAnalyzer
    analyzer = ComparativeAnalyzer()
    tutor_text = "Hello how are you doing"
    student_text = text[:100]
    result = analyzer.analyze(tutor_text, student_text)
    print(f"   Result keys: {list(result.keys())}")
    print(f"   Status: ✓ WORKS")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")

# Test 9: Learner Error Analyzer
print("\n9. Learner Error Analyzer")
try:
    from analyzers.learner_error_analyzer import LearnerErrorAnalyzer
    analyzer = LearnerErrorAnalyzer()
    result = analyzer.analyze(text[:100])
    print(f"   Result: {result}")
    print(f"   Status: ✓ LOADS")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")

# Test 10: Pronunciation Analyzer
print("\n10. Pronunciation Analyzer")
try:
    from analyzers.pronunciation_analyzer import PronunciationAnalyzer
    analyzer = PronunciationAnalyzer()
    result = analyzer.analyze(text[:100])
    print(f"   Result: {result}")
    print(f"   Status: ✓ LOADS")
except Exception as e:
    print(f"   Status: ✗ ERROR - {e}")

print()
print("=" * 60)
print("Testing complete")
