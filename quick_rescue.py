import asyncio
import os
from dotenv import load_dotenv

# Assign result to satisfy lint
_ = load_dotenv()

try:
    import assemblyai as aai
except Exception as e:
    print(f"⚠️ Warning: AssemblyAI import error: {e}")

from ingest_audio import process_and_upload

# Explicitly configure AssemblyAI
AAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if AAI_API_KEY:
    try:
        aai.settings.api_key = AAI_API_KEY
    except Exception as e:
        print(f"⚠️ Could not set aai.settings.api_key: {e}")
else:
    print("❌ ASSEMBLYAI_API_KEY not found in environment.")

# HARDCODED CONFIG FOR RESCUE
AUDIO_FILE = "sessions/Jocelyn_Dec17.mp3" 
STUDENT_NAME = "Jocelyn"

async def run():
    if not os.path.exists(AUDIO_FILE):
        print(f"File not found: {AUDIO_FILE}")
        # Try absolute path just in case
        abs_path = f"/Users/safeSpacesBro/AssemblyAIv2/{AUDIO_FILE}"
        if os.path.exists(abs_path):
            print(f"Found at absolute path: {abs_path}")
            await process_and_upload(abs_path, STUDENT_NAME, "Rescued session via Agent")
        else:
            print("Cannot find file.")
            return
    else:
        await process_and_upload(AUDIO_FILE, STUDENT_NAME, "Rescued session via Agent")

if __name__ == "__main__":
    asyncio.run(run())
