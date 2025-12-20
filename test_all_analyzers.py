#!/usr/bin/env python3
"""
Test all 21 analyzers to see which ones actually work
"""

import sys
import os
sys.path.append('.')

def test_analyzer(analyzer_name, module_path, class_name, test_text="I have been studying English grammar."):
    """Test a single analyzer"""
    try:
        # Import the module
        module = __import__(module_path, fromlist=[class_name])
        analyzer_class = getattr(module, class_name)
        
        # Initialize analyzer
        analyzer = analyzer_class()
        
        # Test with sample text
        result = analyzer.analyze(test_text)
        
        print(f"✅ {analyzer_name}: SUCCESS")
        print(f"   Result: {str(result)[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ {analyzer_name}: FAILED - {str(e)[:50]}...")
        return False

def main():
    print("🧪 TESTING ALL 21 ANALYZERS")
    print("=" * 50)
    
    # List of all analyzers
    analyzers = [
        ("N-gram Analyzer", "analyzers.ngram_analyzer", "NgramAnalyzer"),
        ("Spelling Analyzer", "analyzers.spelling_analyzer", "SpellingAnalyzer"),
        ("POS Analyzer", "analyzers.pos_analyzer", "POSAnalyzer"),
        ("Verb Analyzer", "analyzers.verb_analyzer", "VerbAnalyzer"),
        ("Article Analyzer", "analyzers.article_analyzer", "ArticleAnalyzer"),
        ("Preposition Analyzer", "analyzers.preposition_analyzer", "PrepositionAnalyzer"),
        ("Pronunciation Analyzer", "analyzers.pronunciation_analyzer", "PronunciationAnalyzer"),
        ("Fluency Analyzer", "analyzers.fluency_analyzer", "FluencyAnalyzer"),
        ("Learner Error Analyzer", "analyzers.learner_error_analyzer", "LearnerErrorAnalyzer"),
        ("Phenomena Matcher", "analyzers.phenomena_matcher", "PhenomenaMatcher"),
        ("Comparative Analyzer", "analyzers.comparative_analyzer", "ComparativeAnalyzer"),
        ("Amalgum Analyzer", "analyzers.amalgum_analyzer", "AmalgumAnalyzer"),
        ("Student Corpus Engine", "analyzers.student_corpus_engine", "StudentCorpusEngine"),
        ("Session Analyzer", "analyzers.session_analyzer", "SessionAnalyzer"),
        ("Student Export", "analyzers.student_export", "StudentExport"),
        ("LLM Gateway", "analyzers.llm_gateway", "LLMGateway"),
        ("Live Feedback Agent", "analyzers.live_feedback_agent", "LiveFeedbackAgent"),
        ("Generate Report", "analyzers.generate_report", "GenerateReport"),
        ("Export Low Confidence Words", "analyzers.export_low_confidence_words", "ExportLowConfidenceWords"),
        ("Export Marked with Context", "analyzers.export_marked_with_context", "ExportMarkedWithContext"),
        ("Run Diarization", "analyzers.run_diarization", "RunDiarization"),
    ]
    
    working = 0
    broken = 0
    
    for name, module, class_name in analyzers:
        if test_analyzer(name, module, class_name):
            working += 1
        else:
            broken += 1
        print()
    
    print("=" * 50)
    print(f"📊 RESULTS: {working} working, {broken} broken")
    print(f"🎯 Success rate: {working}/{working+broken} ({working/(working+broken)*100:.1f}%)")

if __name__ == "__main__":
    main()