#!/usr/bin/env python3
"""
FULL PIPELINE: Audio → AssemblyAI → Diarized Transcript → Analysis → GitEnglishHub

Usage: 
  source venv/bin/activate
  python test_full_pipeline.py /path/to/audio.mp3 "Student Name"
"""

import os
import sys
import json
import asyncio
import assemblyai as aai
import httpx
from dotenv import load_dotenv

load_dotenv()

# Config
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
GITENGLISH_API = os.getenv("GITENGLISH_API_BASE", "https://www.gitenglish.com")
MCP_SECRET = os.getenv("MCP_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def get_student_id(student_name: str) -> str:
    """Look up student ID from name."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE not configured, can't look up student")
        return None
    
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    result = supabase.table("students").select("id, first_name, last_name").ilike("first_name", f"%{student_name}%").execute()
    
    if result.data and len(result.data) > 0:
        student = result.data[0]
        print(f"✅ Found student: {student['first_name']} {student.get('last_name', '')} ({student['id'][:8]}...)")
        return student['id']
    
    print(f"❌ Student '{student_name}' not found")
    return None


async def transcribe_with_diarization(audio_path: str):
    """Send audio to AssemblyAI and get diarized transcript."""
    print(f"\n📤 Uploading to AssemblyAI: {audio_path}")
    
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=2,
        punctuate=True,
        format_text=False,  # Keep fillers
        speech_model='slam-1'
    )
    
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path, config)
    
    if transcript.status == "error":
        print(f"❌ Transcription Error: {transcript.error}")
        return None
    
    print(f"✅ Transcription Complete!")
    print(f"   Duration: {transcript.audio_duration}s")
    print(f"   Confidence: {transcript.confidence:.2%}")
    print(f"   Words: {len(transcript.words or [])}")
    print(f"   Utterances: {len(transcript.utterances or [])}")
    
    return transcript


async def send_to_gitenglish(action: str, student_id: str, params: dict) -> dict:
    """Send data to GitEnglishHub for analysis."""
    if not MCP_SECRET:
        print("❌ MCP_SECRET not configured")
        return {"success": False, "error": "MCP_SECRET not configured"}
    
    url = f"{GITENGLISH_API}/api/mcp"
    headers = {
        "Authorization": f"Bearer {MCP_SECRET}",
        "Content-Type": "application/json"
    }
    payload = {
        "action": action,
        "studentId": student_id,
        "params": params
    }
    
    print(f"\n📤 Sending to GitEnglishHub: {action}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ GitEnglishHub Response: success={result.get('success', False)}")
            return result
        else:
            print(f"❌ GitEnglishHub Error ({response.status_code}): {response.text[:200]}")
            return {"success": False, "error": response.text}


async def run_pipeline(audio_path: str, student_name: str):
    """Run the full pipeline."""
    print("=" * 60)
    print("FULL AUDIO PIPELINE TEST")
    print("=" * 60)
    
    # 1. Look up student
    student_id = await get_student_id(student_name)
    if not student_id:
        return
    
    # 2. Transcribe with diarization
    transcript = await transcribe_with_diarization(audio_path)
    if not transcript:
        return
    
    # 3. Build session data
    turns = []
    for utterance in transcript.utterances or []:
        turns.append({
            "speaker": utterance.speaker,
            "transcript": utterance.text,
            "start": utterance.start,
            "end": utterance.end,
            "confidence": utterance.confidence,
            "words": [
                {
                    "text": w.text,
                    "start": w.start,
                    "end": w.end,
                    "confidence": w.confidence,
                    "speaker": w.speaker
                }
                for w in (utterance.words or [])
            ]
        })
    
    # 4. Send to GitEnglishHub for processing
    result = await send_to_gitenglish("ingest.createSession", student_id, {
        "turns": turns,
        "transcriptText": transcript.text,
        "duration": transcript.audio_duration,
        "sessionDate": None,  # Will use current date
        "speakerStudent": "B"  # Assume B is student
    })
    
    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    
    if result.get("success") and result.get("data", {}).get("success"):
        data = result.get("data", {})
        print(f"✅ Session Created: {data.get('sessionId', '?')[:8]}...")
        print(f"   Words Processed: {data.get('extraction', {}).get('wordsProcessed', 0)}")
        print(f"   Corpus Entries: {data.get('extraction', {}).get('corpusEntriesCreated', 0)}")
        print(f"   Phenomena Found: {data.get('extraction', {}).get('phenomenaMatched', 0)}")
        print(f"   Sanity Doc: {data.get('sanityDocId', 'N/A')}")
    else:
        print(f"❌ Pipeline Failed:")
        print(f"   {result.get('error', result.get('data', {}).get('error', 'Unknown error'))}")
    
    # 5. Print sample of diarized transcript
    print("\n" + "=" * 60)
    print("DIARIZED TRANSCRIPT (First 5 turns)")
    print("=" * 60 + "\n")
    
    for turn in turns[:5]:
        print(f"[Speaker {turn['speaker']}]: {turn['transcript'][:100]}...\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_full_pipeline.py /path/to/audio.mp3 'Student Name'")
        print("\nExample:")
        print("  python test_full_pipeline.py ~/recordings/session.mp3 'Carlos'")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    student_name = sys.argv[2]
    
    asyncio.run(run_pipeline(audio_path, student_name))
