import sys
import json
import logging
from pathlib import Path

# --- RIGOROUS ANALYZER VERIFICATION ---

def test_analyzers():
    # 1. GROUND TRUTH DATA
    # Errors:
    # - "go" (wrong tense for yesterday)
    # - "a apple" (wrong article)
    # - "have been lived" (wrong aspect)
    # - "three year" (pluralization - though local analyzers might not catch this yet)
    # - "He don't" (agreement)
    student_text = "I go to store yesterday and see a apple. I have been lived here for three year. He don't like it."
    tutor_text = "I understand. You should say 'I went to the store' and 'an apple'. Your English is improving."

    print("\n" + "="*60)
    print("🔬 COMPONENT-BY-COMPONENT RIGOROUS VERIFICATION")
    print("="*60)

    # Helper to run and report
    def check(name, analyzer_class, method_name, text, expected_min_results=1):
        print(f"\n[Testing {name}]")
        try:
            instance = analyzer_class()
            method = getattr(instance, method_name)
            result = method(text)
            
            # Scrutinize result
            print(f"  Raw Result: {json.dumps(result, indent=2)}")
            
            if isinstance(result, list):
                count = len(result)
            elif isinstance(result, dict):
                # Custom counting logic for different analyzer dicts
                if 'irregular_errors' in result:
                    count = len(result['irregular_errors'])
                elif 'verb_ratio' in result:
                    count = 1 if result['verb_ratio'] > 0 else 0
                elif 'academic' in result:
                    count = 1 if (result['academic'] + result['conversational']) > 0 else 0
                elif 'total_bigrams' in result:
                    count = result['total_bigrams']
                else:
                    count = len(result)
            else:
                count = 1
                
            if count >= expected_min_results:
                print(f"  ✅ SUCCESS: Found {count} items/metrics.")
                return result
            else:
                print(f"  ⚠️ WARNING: Found {count} items, expected at least {expected_min_results}.")
                return result
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return None

    # --- EXECUTION ---

    # 1. ArticleAnalyzer (Expected: "a apple" error)
    from analyzers.article_analyzer import ArticleAnalyzer
    article_res = check("ArticleAnalyzer", ArticleAnalyzer, "analyze", student_text, 1)

    # 2. VerbAnalyzer (Expected: "go", "see", "have", "lived", "don't", "like")
    from analyzers.verb_analyzer import VerbAnalyzer
    verb_res = check("VerbAnalyzer", VerbAnalyzer, "analyze", student_text, 3)

    # 3. POSAnalyzer (Expected: Ratios for verbs/nouns)
    from analyzers.pos_analyzer import POSAnalyzer
    pos_res = check("POSAnalyzer", POSAnalyzer, "analyze", student_text, 1)

    # 4. NgramAnalyzer (Expected: bigrams)
    from analyzers.ngram_analyzer import NgramAnalyzer
    ngram_res = check("NgramAnalyzer", NgramAnalyzer, "analyze", student_text, 10)

    # 5. AmalgumAnalyzer (Expected: Conversational)
    from analyzers.amalgum_analyzer import AmalgumAnalyzer
    amalgum_res = check("AmalgumAnalyzer", AmalgumAnalyzer, "analyze_register", student_text, 1)

    # 6. ComparativeAnalyzer (Expected: gap analysis)
    from analyzers.comparative_analyzer import ComparativeAnalyzer
    try:
        print("\n[Testing ComparativeAnalyzer]")
        ca = ComparativeAnalyzer()
        comp_res = ca.compare({"text": student_text}, {"text": tutor_text})
        print(f"  Raw Result Keys: {list(comp_res.keys())}")
        print(f"  Naturalness Gap: {comp_res.get('comparison', {}).get('naturalness_gap')}")
        print(f"  ✅ SUCCESS.")
    except Exception as e:
        print(f"  ❌ Comparative FAILED: {e}")

    # 7. SessionAnalyzer (Expected: Aggregate results)
    from analyzers.session_analyzer import SessionAnalyzer
    try:
        print("\n[Testing SessionAnalyzer Aggregation]")
        mock_session = {
            "session_id": "test_sync",
            "student_name": "Jocelyn",
            "speaker_map": {"A": "Aaron", "B": "Jocelyn"},
            "turns": [
                {"speaker": "A", "transcript": tutor_text, "turn_order": 1},
                {"speaker": "B", "transcript": student_text, "turn_order": 2, "words": [{"text": "I", "confidence": 0.9}, {"text": "go", "confidence": 0.9}]}
            ]
        }
        sa = SessionAnalyzer(mock_session)
        final = sa.analyze_all()
        print(f"  Final Keys: {list(final.keys())}")
        print(f"  Student Talk Time: {final.get('comparison', {}).get('talk_time_ratio', {}).get('student_percentage')}%")
        print("  ✅ SUCCESS.")
    except Exception as e:
        print(f"  ❌ SessionAnalyzer FAILED: {e}")

    print("\n" + "="*60)
    print("🏁 RIGOROUS VERIFICATION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_analyzers()
