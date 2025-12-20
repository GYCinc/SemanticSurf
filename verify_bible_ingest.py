import asyncio
import os
import logging
from ingest_audio import perform_batch_diarization

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyBible")

async def test_ingest():
    audio_path = "sessions/audio_1766132713.wav"
    student_name = "TestStudent"
    
    print(f"--- TESTING BIBLE COMPLIANCE ON {audio_path} ---")
    
    # This calls the function in ingest_audio.py which we MODIFIED to enforce the Bible
    turns, duration = await perform_batch_diarization(audio_path, student_name)
    
    if turns:
        print(f"\n✅ SUCCESS! Received {len(turns)} turns.")
        print(f"Duration: {duration}s")
        
        # VERIFY BIBLE COMPLIANCE
        print("\n--- INSPECTING OUTPUT FOR BIBLE COMPLIANCE ---")
        
        # 1. Speaker Labels
        speakers = set(t['speaker'] for t in turns)
        print(f"Speakers Found: {speakers}")
        if len(speakers) > 1:
            print("✅ Diarization: PASS (Multiple speakers detected)")
        else:
            print("⚠️ Diarization: WARNING (Only 1 speaker found, but labels field exists)")

        # 2. Raw Text (No Punctuation/Formatting)
        sample_text = turns[0]['transcript']
        print(f"Sample Transcript: '{sample_text}'")
        
        has_caps = any(c.isupper() for c in sample_text)
        has_punct = any(c in ".?!" for c in sample_text)
        
        if not has_punct:
            print("✅ Raw Text: PASS (No punctuation detected)")
        else:
            print("❌ Raw Text: FAIL (Punctuation found!)")
            
        if not has_caps:
             print("✅ Formatting: PASS (No capitalization detected)")
        else:
             print("❌ Formatting: FAIL (Capitalization found!)")

    else:
        print("❌ FAILURE: No turns returned.")

if __name__ == "__main__":
    asyncio.run(test_ingest())
