import os
import sys
import asyncio
import logging
from pathlib import Path

# Setup paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealIngest")

# --- SECRET LOADING ---
MCP_SECRET = None
assembly_env_path = WORKSPACE_ROOT / ".env"

if assembly_env_path.exists():
    try:
        content = assembly_env_path.read_text()
        for line in content.splitlines():
            if line.startswith("MCP_SECRET="):
                MCP_SECRET = line.split("=", 1)[1].strip().strip("'").strip('"')
                os.environ["MCP_SECRET"] = MCP_SECRET
                break
    except Exception as e:
        logger.error(f"Error reading .env: {e}")

if not MCP_SECRET:
    logger.error("❌ MCP_SECRET not found in AssemblyAIv2/.env")
    sys.exit(1)

# Import upload_audio_aai
import upload_audio_aai
from upload_audio_aai import process_and_upload

# DIRECTLY PATCH THE MODULE VARIABLE
upload_audio_aai.GITENGLISH_MCP_SECRET = MCP_SECRET
logger.info("✅ Patched upload_audio_aai.GITENGLISH_MCP_SECRET")

async def run_real():
    audio_path = "/Users/thelaw/ESL 5.0/By Student/Andrea/2025-12-07- andrea_09.37.13.mp3"
    student_name = "Andrea"
    notes = "Real pipeline verification test with Andrea's file."

    logger.info(f"🚀 Starting Real Ingestion for {audio_path}...")
    
    # 1. Ingest
    result = await process_and_upload(audio_path, student_name, notes)
    
    if not result.get('success'):
        logger.error("❌ Ingestion Failed")
        return

    session_id = result.get('sessionId') or result.get('data', {}).get('sessionId')
    logger.info(f"✅ Session Created: {session_id}")
    
    # Analyze the data returned by the Hub
    data = result.get('data', {})
    speaker_counts = data.get('speakerCounts', {})
    
    logger.info("-" * 40)
    logger.info("📊 DIARIZATION VERIFICATION")
    logger.info("-" * 40)
    logger.info(f"   Total Pending Words: {data.get('pendingWords')}")
    logger.info(f"   Tutor (Speaker A):   {speaker_counts.get('A', 0)} words")
    logger.info(f"   Student (Speaker B): {speaker_counts.get('B', 0)} words")
    
    student_words = speaker_counts.get('B', 0)
    
    if student_words > 100:
        logger.info(f"✅ VERIFIED: Captured {student_words} words from student.")
    else:
        logger.error("❌ VERIFICATION FAILED: Student word count too low.")

if __name__ == "__main__":
    asyncio.run(run_real())
