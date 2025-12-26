
import asyncio
import sys
import os
import logging
sys.path.append(os.path.dirname(os.getcwd()))
from AssemblyAIv2.upload_audio_aai import process_and_upload

# Configure logging
logging.basicConfig(level=logging.INFO)

async def run_verification():
    audio_file = "/Users/thelaw/ESL 5.0/By Student/Francisco/AutoMp3Francisco/2025-12-10_16.41.57.mp3"
    student_name = "Francisco"
    notes = "Verification Run - Automated"
    
    print(f"🚀 Starting verification for {student_name} with {audio_file}")
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return

    try:
        # We perform the real ingestion to generate artifacts.
        # The send_to_gitenglish might fail if MCP secret is missing/invalid, 
        # but we care most about the local artifacts in .session_captures
        
        await process_and_upload(audio_file, student_name, notes)
        print("✅ Verification run finished")
        
    except Exception as e:
        print(f"❌ Verification run failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_verification())
