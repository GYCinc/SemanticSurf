import asyncio
import json
import logging
import os
from pathlib import Path
from datetime import datetime
import uuid

# Mocking the main script imports and environment
os.environ['MCP_SECRET'] = 'test_secret'
os.environ['GITENGLISH_API_BASE'] = 'http://localhost:3000' # Mock base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FullPipelineTest")

async def test_full_flow():
    from main import upload_analysis_to_supabase
    
    print("\n--- 🚀 STARTING FULL PIPELINE INTEGRATION TEST ---\n")
    
    # 1. Create a real-looking session file using session_id
    session_id = "test_sess_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = Path(f"sessions/{session_id}.json")
    
    session_data = {
        "session_id": session_id,
        "student_name": "Jocelyn",
        "start_time": datetime.now().isoformat(),
        "speaker_map": {"A": "Aaron", "B": "Jocelyn"},
        "notes": "Student struggled with past tense and articles.",
        "turns": [
            {
                "turn_order": 1,
                "speaker": "A",
                "transcript": "Hello Jocelyn, how was your day?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "turn_order": 2,
                "speaker": "B",
                "transcript": "I go to store yesterday and see a apple. It is very good.",
                "timestamp": datetime.now().isoformat(),
                "analysis": {"speaking_rate_wpm": 110, "pauses": [{"duration_ms": 1200, "start_ms": 500}]},
                "words": [
                    {"text": "I", "confidence": 0.99, "start_ms": 0, "end_ms": 100},
                    {"text": "go", "confidence": 0.99, "start_ms": 100, "end_ms": 200},
                    {"text": "to", "confidence": 0.99, "start_ms": 200, "end_ms": 300},
                    {"text": "store", "confidence": 0.99, "start_ms": 300, "end_ms": 400},
                    {"text": "yesterday", "confidence": 0.99, "start_ms": 400, "end_ms": 500}
                ]
            }
        ]
    }
    
    with open(session_path, 'w') as f:
        json.dump(session_data, f)
        
    print(f"Created synthetic session file: {session_path}")

    # 2. Run the pipeline
    # We pass the metadata dictionary that on_terminated expects
    upload_data = {
        "session_file_path": str(session_path),
        "audio_path": None, # Skip diarization for this test
        "duration_seconds": 60
    }
    
    try:
        # Note: This will attempt a real Gemini call if API key is present
        # and a real Hub call. We want to see if it reaches the Hub call!
        await upload_analysis_to_supabase(upload_data)
        print("\n✅ Pipeline reached final stage (API Upload).")
    except Exception as e:
        print(f"\n❌ Pipeline CRASHED: {e}")
    finally:
        # Clean up
        if session_path.exists():
            session_path.unlink()

    print("\n--- 🏁 FULL PIPELINE TEST COMPLETE ---\n")

if __name__ == "__main__":
    asyncio.run(test_full_flow())