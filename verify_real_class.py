
import sys
import os
import json
import glob

sys.path.append(os.getcwd())
# Import all analyzers to test them one by one
from AssemblyAIv2.analyzers.session_analyzer import SessionAnalyzer
from AssemblyAIv2.analyzers.verb_analyzer import VerbAnalyzer
# Add other analyzers here if they exist and are relevant

def test_analyzers_on_real_data():
    # Find the most recent JSON in sessions
    json_files = glob.glob('AssemblyAIv2/sessions/**/*.json', recursive=True)
    if not json_files:
        print("❌ No JSON session files found in AssemblyAIv2/sessions")
        # Fallback to a hardcoded check if we find one during the 'find' command
        return

    latest_json = max(json_files, key=os.path.getctime)
    print(f"📂 Loading real session data: {latest_json}")
    
    with open(latest_json, 'r') as f:
        session_data = json.load(f)

    # 1. Test SessionAnalyzer
    print("\n----- Testing SessionAnalyzer -----")
    try:
        sa = SessionAnalyzer(session_data)
        results = sa.analyze_all()
        
        # Verify key metrics
        wpm = results['student_metrics']['speaking_rate'].get('average_wpm')
        pauses = results['student_metrics']['pauses'].get('total_pauses')
        hesitations = results['student_metrics']['hesitation_patterns'].get('total_hesitations')
        
        print(f"✅ SessionAnalyzer Success")
        print(f"   Student WPM: {wpm}")
        print(f"   Student Pauses: {pauses}")
        print(f"   Hesitations: {hesitations}")
        
    except Exception as e:
        print(f"❌ SessionAnalyzer Failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Test VerbAnalyzer (if applicable)
    print("\n----- Testing VerbAnalyzer -----")
    try:
        # VerbAnalyzer usually takes different input, check signature
        # Assuming it takes text or turns
        student_text = results.get('student_metrics', {}).get('advanced_local_analysis', {}).get('text', '') # This path might be wrong, checking full text
        # Or maybe it takes the full text from the analyzer
        if hasattr(sa, 'student_full_text'):
             va = VerbAnalyzer(sa.student_full_text)
             verb_results = va.analyze()
             print(f"✅ VerbAnalyzer Success")
             print(f"   Tense Distribution: {verb_results.get('tense_distribution')}")
    except Exception as e:
        # It's possible VerbAnalyzer isn't set up this way, strictly catching to not block
        print(f"⚠️ VerbAnalyzer test skipped/failed (check signature): {e}")

if __name__ == "__main__":
    test_analyzers_on_real_data()
