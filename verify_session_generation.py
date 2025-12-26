
import sys
import json
from pathlib import Path

# Fix Path: Add the PARENT of AssemblyAIv2 to sys.path so we can do 'from AssemblyAIv2...'
# WORKSPACE_ROOT is /Users/safeSpacesBro/AssemblyAIv2
WORKSPACE_ROOT = Path(__file__).resolve().parent
sys.path.append(str(WORKSPACE_ROOT.parent)) # Go up one level

from AssemblyAIv2.analyzers.session_analyzer import SessionAnalyzer

def test_session_generation():
    print("🧪 Testing SessionAnalyzer Full Flow...")
    
    # LOAD REAL FRANCISCO DATA using the _words.json as the turns source
    # We need to construct a fake 'session_data' that looks like what run_tiered_analysis creates
    try:
        base_path = WORKSPACE_ROOT / ".session_captures/Francisco/2025-12-26/12-45-00_Francisco"
        
        with open(str(base_path) + "_words.json", 'r') as f:
            all_turns = json.load(f)
            
        with open(str(base_path) + "_diarized.txt", 'r') as f:
            punctuated = f.read()

        with open(str(base_path) + "_raw.txt", 'r') as f:
            raw = f.read()
            
        print(f"📄 Loaded {len(all_turns)} turns.")
        
        session_data = {
            "session_id": "TEST_SESSION_FRANCISCO_001",
            "student_name": "Francisco",
            "teacher_name": "Tutor",
            "speaker_map": {"A": "Tutor", "B": "Francisco"}, # Assuming B is student based on typical AAI
            "turns": all_turns,
            "punctuated_transcript": punctuated,
            "raw_transcript": raw
        }
        
        analyzer = SessionAnalyzer(session_data)
        metrics = analyzer.analyze_all()
        
        # VERIFY OUTPUTS
        print("\n--- RESULTS ---")
        print(f"✅ Comparison Keys: {list(metrics['comparison'].keys())}")
        if 'linguistics' in metrics['comparison'] and metrics['comparison']['linguistics']:
            print("✅ ComparativeAnalyzer output found!")
        else:
            print("❌ ComparativeAnalyzer output MISSING!")

        if 'corpus_review' in metrics:
            print("✅ Corpus Review generated!")
            print(f"   Items: {len(metrics['corpus_review'].get('proposed_corpus_additions', []))}")
        else:
            print("❌ Corpus Review MISSING!")

        # Check file existence
        inbox = WORKSPACE_ROOT / "AssemblyAIv2/admin_inbox"
        files = list(inbox.glob("corpus_review_*.json"))
        if files:
            print(f"✅ Inbox File Created: {files[0].name}")
        else:
             print("❌ Inbox File NOT Created!")
             
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_generation()
