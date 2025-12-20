import logging
import sys
from analyzers.session_analyzer import SessionAnalyzer
from analyzers.pos_analyzer import POSAnalyzer
from analyzers.ngram_analyzer import NgramAnalyzer
from analyzers.verb_analyzer import VerbAnalyzer
from analyzers.article_analyzer import ArticleAnalyzer
from analyzers.preposition_analyzer import PrepositionAnalyzer
from analyzers.phenomena_matcher import ErrorPhenomenonMatcher

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("AnalyzerCheck")

SYNTHETIC_TEXT = "I have went to the store yesterday because I needing to buy some milk. Um, actually, I wanted cheese too. The shop was closed, so I am sad. Do you thinking it opens tomorrow? I hope it opening."

def test_analyzer(name, analyzer_class, method_name="analyze", *args):
    print(f"\n🧪 Testing {name}...")
    try:
        analyzer = analyzer_class()
        
        # Special case for phenomena matcher async init
        if name == "ErrorPhenomenonMatcher":
            import asyncio
            asyncio.run(analyzer.initialize())
            result = analyzer.match(SYNTHETIC_TEXT)
        elif name == "SessionAnalyzer":
            # SessionAnalyzer takes a dict
            session_data = {
                "turns": [{
                    "transcript": SYNTHETIC_TEXT,
                    "words": [{"text": w} for w in SYNTHETIC_TEXT.split()],
                    "analysis": {"pauses": []}
                }],
                "speaker_map": {"A": "Student"},
                "student_name": "Student",
                "teacher_name": "Tutor"
            }
            analyzer = analyzer_class(session_data)
            result = analyzer.analyze_all()
        else:
            method = getattr(analyzer, method_name)
            result = method(SYNTHETIC_TEXT, *args)
            
        print(f"✅ {name} Result Summary:")
        if isinstance(result, list):
            print(f"   Count: {len(result)}")
            if result: print(f"   Sample: {result[0]}")
        elif isinstance(result, dict):
            keys = list(result.keys())[:5]
            print(f"   Keys: {keys}")
            if "pos_distribution" in result: print(f"   POS: {result['pos_distribution']}")
            if "irregular_errors" in result: print(f"   Verb Errors: {result['irregular_errors']}")
            if "comparison" in result: print("   Comparison generated.")
        else:
            print(f"   Result: {result}")
            
    except Exception as e:
        print(f"❌ {name} FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"📜 Input Text: '{SYNTHETIC_TEXT}'\n")
    
    test_analyzer("SessionAnalyzer", SessionAnalyzer)
    test_analyzer("POSAnalyzer", POSAnalyzer)
    test_analyzer("NgramAnalyzer", NgramAnalyzer)
    test_analyzer("VerbAnalyzer", VerbAnalyzer)
    test_analyzer("ArticleAnalyzer", ArticleAnalyzer)
    test_analyzer("PrepositionAnalyzer", PrepositionAnalyzer)
    test_analyzer("ErrorPhenomenonMatcher", ErrorPhenomenonMatcher)
