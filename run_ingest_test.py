
import asyncio
import os
import sys
from pathlib import Path

# Setup Path
WORKSPACE_ROOT = Path(__file__).resolve().parent
sys.path.append(str(WORKSPACE_ROOT))

# Iimport upload_audio_aai
from upload_audio_aai import process_and_upload

async def main():
    print("🚀 STARTING AUTOMATED INGEST TEST")
    
    # Configuration
    # Using an existing file found in previous steps
    audio_path = str(WORKSPACE_ROOT / "sessions/Andrea_Oct19.mp3") 
    student_name = "Andrea"
    notes = "Test session for auto-publishing card verification."
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        # Try finding another file if this one is missing
        import glob
        files = glob.glob(str(WORKSPACE_ROOT / "sessions/*.mp3"))
        if files:
            audio_path = files[0]
            print(f"⚠️ Switching to found file: {audio_path}")
        else:
            print("❌ No MP3 files found in sessions/")
            return

    print(f"📂 Processing: {audio_path}")
    print(f"qs Student: {student_name}")
    
    # Run
    result = await process_and_upload(
        audio_path=audio_path, 
        student_name=student_name, 
        notes=notes
    )
    
    print("\n🏁 RESULT:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
