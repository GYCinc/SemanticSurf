
import sys
import os
import json
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add workspace root to path
# We are in AssemblyAIv2/scripts. Parent is AssemblyAIv2. Grandparent is the workspace root.
# We want to be able to import upload_audio_aai.
# If we run from AssemblyAIv2/, then upload_audio_aai is in CWD.
sys.path.append(os.getcwd())

import upload_audio_aai

async def verify_payload():
    print("🧪 Starting Payload Verification for upload_audio_aai.py...")

    # Mock Data
    mock_diar_result = {
        "turns": [
            {"speaker": "A", "transcript": "Hello.", "start": 0, "end": 1000, "confidence": 0.9, "words": []},
            {"speaker": "B", "transcript": "Hi there.", "start": 1000, "end": 2000, "confidence": 0.8, "words": []}
        ],
        "duration": 2.0,
        "punctuated_text": "Hello. Hi there.",
        "sentences": [],
        "raw_transcript_text": "hello hi there",
        "diarized_transcript_text": "Hello. Hi there.",
        "raw_response_diar": {},
        "raw_response_raw": {}
    }

    mock_llm_analysis = {
        "termination": {"reason": "success"},
        "response": "Good session.",
        "annotated_errors": [
            {"quote": "I go store", "correction": "I went to the store", "category": "Grammar", "explanation": "Past tense"}
        ],
        "student_profile": {"boss_notes": "Improving"}
    }

    # Patch Everything
    with patch('upload_audio_aai.perform_batch_diarization', return_value=mock_diar_result) as mock_diar, \
         patch('upload_audio_aai.generate_llm_analysis', return_value=mock_llm_analysis) as mock_llm, \
         patch('upload_audio_aai.send_to_gitenglish', return_value={"success": True, "data": {"sessionId": "mock-session-id"}}) as mock_send, \
         patch('upload_audio_aai.calculate_file_hash', return_value="dummy_hash"):

        # Run process_and_upload
        print("   🏃 Running process_and_upload (mocked)...")
        await upload_audio_aai.process_and_upload("dummy_audio.wav", "Test Student", "Notes")

        # Verify send_to_gitenglish calls
        if mock_send.call_count == 0:
            print("❌ send_to_gitenglish was NOT called!")
            return False
            
        # Get arguments
        call_args = mock_send.call_args
        # signature: action, student_id_or_name, params
        action = call_args[0][0] if call_args[0] else call_args[1].get('action')
        student = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('student_id_or_name')
        params = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('params')

        print(f"   📨 Action: {action}")
        print(f"   👤 Student: {student}")
        
        # Assertions
        errors = []
        if action != "ingest.createSession":
            errors.append(f"Expected action 'ingest.createSession', got '{action}'")
        
        if not params:
            errors.append("Params missing")
        else:
            if params.get('llmGatewayAnalysis') != "Good session.":
                errors.append("llmGatewayAnalysis mismatch")
            
            phenomena = params.get('llmGatewayPhenomena', [])
            if not phenomena or len(phenomena) == 0:
                 errors.append("llmGatewayPhenomena missing or empty")
            else:
                p = phenomena[0]
                if p.get('item') != "I go store" or p.get('correction') != "I went to the store":
                    errors.append(f"Phenomena mismatch: {p}")

        if errors:
            print("❌ Verification FAILED:")
            for e in errors:
                print(f"   - {e}")
            return False
            
        print("✅ Payload Logic Verified Successfully!")
        print("   Structure matches GitEnglishHub expectations.")
        return True

if __name__ == "__main__":
    try:
        asyncio.run(verify_payload())
    except Exception as e:
        print(f"❌ Script Error: {e}")
        import traceback
        traceback.print_exc()
