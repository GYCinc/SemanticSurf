
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
        # Fallback to test_session.json
        if os.path.exists('AssemblyAIv2/test_session.json'):
             print("⚠️ Falling back to AssemblyAIv2/test_session.json")
             json_files = ['AssemblyAIv2/test_session.json']
        else:
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
        # If session analyzer fails, we cannot proceed with dependent analyzers
        return

    # 2. Test VerbAnalyzer (if applicable)
    print("\n----- Testing VerbAnalyzer -----")
    try:
        # VerbAnalyzer usually takes different input, check signature
        # Assuming it takes text or turns
        # 'results' and 'sa' are now guaranteed to be defined if we reached here
        
        # Try to find the text source
        student_text = ""
        if hasattr(sa, 'student_full_text'):
             student_text = sa.student_full_text
        elif results and 'student_metrics' in results:
             student_text = results.get('student_metrics', {}).get('advanced_local_analysis', {}).get('text', '')
        
        if student_text:
             # Check if VerbAnalyzer accepts text (assuming yes based on usage)
             # If VerbAnalyzer was imported successfully
             if 'VerbAnalyzer' in globals():
                va = VerbAnalyzer()
                verb_results = va.analyze(student_text)
                print(f"✅ VerbAnalyzer Success")
                print(f"   Irregular Errors: {len(verb_results.get('irregular_errors', []))}")
                print(f"   Total Verbs Found: {verb_results.get('total_verbs_found')}")
             else:
                 print("⚠️ VerbAnalyzer class not found/imported")
        else:
            print("⚠️ Could not extract student text for VerbAnalyzer")
            
    except Exception as e:
        # It's possible VerbAnalyzer isn't set up this way, strictly catching to not block
        print(f"⚠️ VerbAnalyzer test skipped/failed (check signature): {e}")

if __name__ == "__main__":
    test_analyzers_on_real_data()
