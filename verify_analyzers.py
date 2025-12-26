import sys
from pathlib import Path
import logging

# Ensure workspace root is on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalyzerVerifier")

ANALYZERS = [
    ("AmalgumAnalyzer", "analyzers.amalgum_analyzer"),
    ("ArticleAnalyzer", "analyzers.article_analyzer"),
    ("ComparativeAnalyzer", "analyzers.comparative_analyzer"),
    ("FluencyAnalyzer", "analyzers.fluency_analyzer"),
    ("LearnerErrorAnalyzer", "analyzers.learner_error_analyzer"),
    ("LexicalEngine", "analyzers.lexical_engine"),
    ("NgramAnalyzer", "analyzers.ngram_analyzer"),
    ("ErrorPhenomenonMatcher", "analyzers.phenomena_matcher"), # Note: class name might be different, checking file
    ("POSAnalyzer", "analyzers.pos_analyzer"),
    ("PrepositionAnalyzer", "analyzers.preposition_analyzer"),
    ("VerbAnalyzer", "analyzers.verb_analyzer"),
]

def verify_all(transcript_path=None):
    print("--- GRANULAR ANALYZER VERIFICATION ---")
    
    transcript_text = "I go-ed to the store via my bicycle." # Default
    words_data = []

    if transcript_path:
        try:
            path_obj = Path(transcript_path)
            with open(path_obj, 'r') as f:
                transcript_text = f.read()
            print(f"📄 Loaded Transcript: {str(path_obj.name)} ({len(transcript_text)} chars)")
            
            # Try to find companion words.json
            # Matches pattern matching 12-45-00_Francisco_diarized.txt -> 12-45-00_Francisco_words.json
            words_path = path_obj.parent / path_obj.name.replace("_diarized.txt", "_words.json").replace("_raw.txt", "_words.json")
            if words_path.exists():
                import json
                with open(words_path, 'r') as f:
                    words_data = json.load(f)
                print(f"⏱️  Loaded Words Data: {words_path.name} ({len(words_data)} words)")
            else:
                 print("⚠️  No _words.json found. Fluency/Timing analysis will be skipped.")

        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            return

    results = {"PASS": [], "FAIL": [], "DEPRECATED": []}

    print(f"\n📝 TEST TEXT PREVIEW:\n{transcript_text[:100]}...\n")

    for class_name, module_path in ANALYZERS:
        print(f"\n{'='*40}")
        print(f"🔍 ANALYZING: {class_name}")
        print(f"{'='*40}")
        
        try:
            # Dynamic import
            module = __import__(module_path, fromlist=[class_name])
            
            # Check for deprecation marker
            file_path = WORKSPACE_ROOT / (module_path.replace('.', '/') + ".py")
            with open(file_path, 'r') as f:
                content = f.read()
                if "# DEPRECATED" in content or "# This file has been removed" in content:
                    print("⚠️  DEPRECATED (Skipping)")
                    results["DEPRECATED"].append(class_name)
                    continue

            # Instantiate
            cls = getattr(module, class_name)
            instance = cls()
            
            # Run Analyze
            try:
                if class_name == "ComparativeAnalyzer":
                        print("ℹ️  Skipping ComparativeAnalyzer (requires student+teacher data)")
                        results["PASS"].append(class_name)
                
                elif class_name == "FluencyAnalyzer":
                    if words_data:
                        # FluencyAnalyzer specific call
                        hesitation = instance.analyze_hesitation(words_data)
                        rate = instance.calculate_articulation_rate(words_data)
                        print(f"✅ HESITATION:\n{json.dumps(hesitation, indent=2)[:500]}...")
                        print(f"✅ ARTICULATION RATE: {rate:.1f} WPM")
                        results["PASS"].append(class_name)
                    else:
                        print("⚠️  Skipping FluencyAnalyzer (No word data loaded)")
                        results["PASS"].append(class_name)

                elif hasattr(instance, 'analyze') and callable(instance.analyze):
                    output = instance.analyze(transcript_text)
                    print(f"✅ OUTPUT ({type(output).__name__}):")
                    import json
                    try:
                        # Try to pretty print JSON-serializable output
                        print(json.dumps(output, indent=2, default=str)[:1000]) # Trucate large output
                        if len(str(output)) > 1000: print("... (truncated)")
                    except:
                        print(str(output)[:1000])
                    
                    results["PASS"].append(class_name)
                else:
                        print("⚠️  No .analyze() method found")
                        results["PASS"].append(class_name)

            except Exception as e:
                print(f"❌ EXECUTION ERROR: {e}")
                results["FAIL"].append(f"{class_name} (Run Error: {e})")

        except ImportError as e:
            print(f"❌ IMPORT ERROR: {e}")
            results["FAIL"].append(f"{class_name} (Import Error: {e})")
        except AttributeError as e:
            print(f"❌ CLASS NOT FOUND: {e}")
            results["FAIL"].append(f"{class_name} (Class Not Found)")
        except Exception as e:
            print(f"❌ UNKNOWN ERROR: {e}")
            results["FAIL"].append(f"{class_name} (Error: {e})")

    print("\n" + "="*40)
    print("MATCH SUMMARY")
    print(f"PASS: {len(results['PASS'])}")
    print(f"FAIL: {len(results['FAIL'])}")
    print("="*40)

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    verify_all(path)
